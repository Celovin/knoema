#pragma once

#include "Components/ActorComponent.h"
#include "LuvoireClient.h"
#include "NPCAgentComponent.generated.h"

UCLASS(ClassGroup = (Luvoire), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class LUVOIREUNREAL_API UNPCAgentComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UNPCAgentComponent();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Luvoire")
    FString BaseUrl = TEXT("http://127.0.0.1:8000");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Luvoire")
    FString ApiKey;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Luvoire")
    FString BootstrapSimulationJson;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Luvoire")
    FString SimulationId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Luvoire")
    float PollIntervalSeconds = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Luvoire")
    bool bAutoCreateSimulation = true;

    UPROPERTY(BlueprintReadOnly, Category = "Luvoire")
    TObjectPtr<ULuvoireClient> Client;

    UFUNCTION(BlueprintCallable, Category = "Luvoire")
    void StartScenario();

    UFUNCTION(BlueprintCallable, Category = "Luvoire")
    void StopScenario();

    UFUNCTION(BlueprintCallable, Category = "Luvoire")
    void InjectWorldEvent(const FString& EventJson);

    UFUNCTION(BlueprintPure, Category = "Luvoire")
    FString GetSimulationState() const;

protected:
    virtual void BeginPlay() override;
    virtual void TickComponent(
        float DeltaTime,
        ELevelTick TickType,
        FActorComponentTickFunction* ThisTickFunction
    ) override;

private:
    float PollAccumulator = 0.0f;

    void EnsureClient();
};
