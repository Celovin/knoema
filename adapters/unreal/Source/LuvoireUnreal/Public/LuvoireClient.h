#pragma once

#include "CoreMinimal.h"
#include "HttpFwd.h"
#include "Templates/Function.h"
#include "UObject/Object.h"
#include "LuvoireClient.generated.h"

USTRUCT(BlueprintType)
struct LUVOIREUNREAL_API FLuvoireSimulationStatus
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Luvoire")
    FString SimulationId;

    UPROPERTY(BlueprintReadOnly, Category = "Luvoire")
    FString Status = TEXT("idle");

    UPROPERTY(BlueprintReadOnly, Category = "Luvoire")
    int32 CompletedTicks = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Luvoire")
    int32 TotalTicks = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Luvoire")
    FString Error;
};

UCLASS(BlueprintType)
class LUVOIREUNREAL_API ULuvoireClient : public UObject
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Luvoire")
    FString BaseUrl = TEXT("http://127.0.0.1:8000");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Luvoire")
    FString ApiKey;

    UPROPERTY(BlueprintReadOnly, Category = "Luvoire")
    FLuvoireSimulationStatus LastStatus;

    UPROPERTY(BlueprintReadOnly, Category = "Luvoire")
    FString LastRawResponse;

    UPROPERTY(BlueprintReadOnly, Category = "Luvoire")
    FString LastError;

    UFUNCTION(BlueprintCallable, Category = "Luvoire")
    void Configure(const FString& InBaseUrl, const FString& InApiKey);

    UFUNCTION(BlueprintCallable, Category = "Luvoire")
    void CreateSimulation(const FString& RequestJson);

    UFUNCTION(BlueprintCallable, Category = "Luvoire")
    void PollSimulation(const FString& SimulationId);

    UFUNCTION(BlueprintCallable, Category = "Luvoire")
    void InjectEvent(const FString& SimulationId, const FString& EventJson);

    UFUNCTION(BlueprintPure, Category = "Luvoire")
    bool HasActiveSimulation() const;

    const FString& GetActiveSimulationId() const
    {
        return ActiveSimulationId;
    }

    const FLuvoireSimulationStatus& GetLastStatus() const
    {
        return LastStatus;
    }

private:
    FString ActiveSimulationId;

    void SendJsonRequest(
        const FString& Verb,
        const FString& Path,
        const FString& Body,
        TFunction<void(FHttpRequestPtr, FHttpResponsePtr, bool)> OnCompleted
    );

    void ApplyAuthHeader(const TSharedRef<IHttpRequest, ESPMode::ThreadSafe>& Request) const;
    void UpdateStatusFromJson(const FString& ResponseBody);
    static FString NormalizeBaseUrl(const FString& InBaseUrl);
};
