#pragma once

#include "Components/ActorComponent.h"
#include "KnoemaClient.h"
#include "NPCAgentComponent.generated.h"

UCLASS(ClassGroup = (Knoema), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class KNOEMAUNREAL_API UNPCAgentComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UNPCAgentComponent();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Knoema")
    FString BaseUrl = TEXT("http://127.0.0.1:8000");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Knoema")
    FString ApiKey;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Knoema")
    FString BootstrapSimulationJson;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Knoema")
    FString SimulationId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Knoema")
    float PollIntervalSeconds = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Knoema")
    bool bAutoCreateSimulation = true;

    UPROPERTY(BlueprintReadOnly, Category = "Knoema")
    TObjectPtr<UKnoemaClient> Client;

    UFUNCTION(BlueprintCallable, Category = "Knoema")
    void StartScenario();

    UFUNCTION(BlueprintCallable, Category = "Knoema")
    void StopScenario();

    UFUNCTION(BlueprintCallable, Category = "Knoema")
    void InjectWorldEvent(const FString& EventJson);

    UFUNCTION(BlueprintPure, Category = "Knoema")
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
