#include "NPCAgentComponent.h"

#include "GameFramework/Actor.h"

UNPCAgentComponent::UNPCAgentComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UNPCAgentComponent::BeginPlay()
{
    Super::BeginPlay();
    EnsureClient();
    if (bAutoCreateSimulation && !BootstrapSimulationJson.IsEmpty())
    {
        StartScenario();
    }
}

void UNPCAgentComponent::TickComponent(
    float DeltaTime,
    ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction
)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!Client || PollIntervalSeconds <= 0.0f)
    {
        return;
    }

    PollAccumulator += DeltaTime;
    if (PollAccumulator < PollIntervalSeconds)
    {
        return;
    }

    PollAccumulator = 0.0f;
    if (!SimulationId.IsEmpty() || Client->HasActiveSimulation())
    {
        Client->PollSimulation(SimulationId);
        SimulationId = Client->GetActiveSimulationId();
    }
}

void UNPCAgentComponent::StartScenario()
{
    EnsureClient();
    if (Client && !BootstrapSimulationJson.IsEmpty())
    {
        Client->CreateSimulation(BootstrapSimulationJson);
    }
}

void UNPCAgentComponent::StopScenario()
{
    SimulationId.Reset();
    PollAccumulator = 0.0f;
}

void UNPCAgentComponent::InjectWorldEvent(const FString& EventJson)
{
    EnsureClient();
    if (Client)
    {
        Client->InjectEvent(SimulationId, EventJson);
    }
}

FString UNPCAgentComponent::GetSimulationState() const
{
    return Client ? Client->GetLastStatus().Status : TEXT("idle");
}

void UNPCAgentComponent::EnsureClient()
{
    if (Client)
    {
        return;
    }

    Client = NewObject<ULuvoireClient>(this, TEXT("LuvoireClient"));
    if (Client)
    {
        Client->Configure(BaseUrl, ApiKey);
    }
}
