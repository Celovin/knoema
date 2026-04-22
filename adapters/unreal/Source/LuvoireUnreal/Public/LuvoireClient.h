#pragma once

#include "CoreMinimal.h"
#include "HttpFwd.h"
#include "Templates/Function.h"
#include "UObject/Object.h"
#include "KnoemaClient.generated.h"

USTRUCT(BlueprintType)
struct KNOEMAUNREAL_API FKnoemaSimulationStatus
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Knoema")
    FString SimulationId;

    UPROPERTY(BlueprintReadOnly, Category = "Knoema")
    FString Status = TEXT("idle");

    UPROPERTY(BlueprintReadOnly, Category = "Knoema")
    int32 CompletedTicks = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Knoema")
    int32 TotalTicks = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Knoema")
    FString Error;
};

UCLASS(BlueprintType)
class KNOEMAUNREAL_API UKnoemaClient : public UObject
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Knoema")
    FString BaseUrl = TEXT("http://127.0.0.1:8000");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Knoema")
    FString ApiKey;

    UPROPERTY(BlueprintReadOnly, Category = "Knoema")
    FKnoemaSimulationStatus LastStatus;

    UPROPERTY(BlueprintReadOnly, Category = "Knoema")
    FString LastRawResponse;

    UPROPERTY(BlueprintReadOnly, Category = "Knoema")
    FString LastError;

    UFUNCTION(BlueprintCallable, Category = "Knoema")
    void Configure(const FString& InBaseUrl, const FString& InApiKey);

    UFUNCTION(BlueprintCallable, Category = "Knoema")
    void CreateSimulation(const FString& RequestJson);

    UFUNCTION(BlueprintCallable, Category = "Knoema")
    void PollSimulation(const FString& SimulationId);

    UFUNCTION(BlueprintCallable, Category = "Knoema")
    void InjectEvent(const FString& SimulationId, const FString& EventJson);

    UFUNCTION(BlueprintPure, Category = "Knoema")
    bool HasActiveSimulation() const;

    const FString& GetActiveSimulationId() const
    {
        return ActiveSimulationId;
    }

    const FKnoemaSimulationStatus& GetLastStatus() const
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
