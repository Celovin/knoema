#include "KnoemaClient.h"

#include "Dom/JsonObject.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

void UKnoemaClient::Configure(const FString& InBaseUrl, const FString& InApiKey)
{
    BaseUrl = NormalizeBaseUrl(InBaseUrl);
    ApiKey = InApiKey;
}

void UKnoemaClient::CreateSimulation(const FString& RequestJson)
{
    SendJsonRequest(
        TEXT("POST"),
        TEXT("/simulations"),
        RequestJson,
        [this](FHttpRequestPtr Request, FHttpResponsePtr Response, bool bSucceeded)
        {
            if (!bSucceeded || !Response.IsValid())
            {
                LastError = TEXT("CreateSimulation request failed.");
                return;
            }

            LastRawResponse = Response->GetContentAsString();
            UpdateStatusFromJson(LastRawResponse);
            if (!LastStatus.SimulationId.IsEmpty())
            {
                ActiveSimulationId = LastStatus.SimulationId;
            }
        }
    );
}

void UKnoemaClient::PollSimulation(const FString& SimulationId)
{
    const FString TargetId = !SimulationId.IsEmpty() ? SimulationId : ActiveSimulationId;
    if (TargetId.IsEmpty())
    {
        LastError = TEXT("PollSimulation requires a simulation id.");
        return;
    }

    SendJsonRequest(
        TEXT("GET"),
        FString::Printf(TEXT("/simulations/%s"), *TargetId),
        FString(),
        [this, TargetId](FHttpRequestPtr Request, FHttpResponsePtr Response, bool bSucceeded)
        {
            if (!bSucceeded || !Response.IsValid())
            {
                LastError = FString::Printf(TEXT("PollSimulation failed for %s."), *TargetId);
                return;
            }

            LastRawResponse = Response->GetContentAsString();
            UpdateStatusFromJson(LastRawResponse);
            if (LastStatus.SimulationId.IsEmpty())
            {
                LastStatus.SimulationId = TargetId;
            }
            ActiveSimulationId = LastStatus.SimulationId;
        }
    );
}

void UKnoemaClient::InjectEvent(const FString& SimulationId, const FString& EventJson)
{
    const FString TargetId = !SimulationId.IsEmpty() ? SimulationId : ActiveSimulationId;
    if (TargetId.IsEmpty())
    {
        LastError = TEXT("InjectEvent requires a simulation id.");
        return;
    }

    SendJsonRequest(
        TEXT("POST"),
        FString::Printf(TEXT("/simulations/%s/events"), *TargetId),
        EventJson,
        [this](FHttpRequestPtr Request, FHttpResponsePtr Response, bool bSucceeded)
        {
            if (!bSucceeded || !Response.IsValid())
            {
                LastError = TEXT("InjectEvent request failed.");
                return;
            }

            LastRawResponse = Response->GetContentAsString();
        }
    );
}

bool UKnoemaClient::HasActiveSimulation() const
{
    return !ActiveSimulationId.IsEmpty();
}

void UKnoemaClient::SendJsonRequest(
    const FString& Verb,
    const FString& Path,
    const FString& Body,
    TFunction<void(FHttpRequestPtr, FHttpResponsePtr, bool)> OnCompleted
)
{
    const TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(NormalizeBaseUrl(BaseUrl) + Path);
    Request->SetVerb(Verb);
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    ApplyAuthHeader(Request);
    if (!Body.IsEmpty())
    {
        Request->SetContentAsString(Body);
    }

    Request->OnProcessRequestComplete().BindLambda(
        [Callback = MoveTemp(OnCompleted)](FHttpRequestPtr InRequest, FHttpResponsePtr InResponse, bool bSucceeded)
        {
            Callback(InRequest, InResponse, bSucceeded);
        }
    );
    Request->ProcessRequest();
}

void UKnoemaClient::ApplyAuthHeader(
    const TSharedRef<IHttpRequest, ESPMode::ThreadSafe>& Request
) const
{
    if (!ApiKey.IsEmpty())
    {
        Request->SetHeader(TEXT("Authorization"), FString::Printf(TEXT("Bearer %s"), *ApiKey));
    }
}

void UKnoemaClient::UpdateStatusFromJson(const FString& ResponseBody)
{
    TSharedPtr<FJsonObject> Payload;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseBody);
    if (!FJsonSerializer::Deserialize(Reader, Payload) || !Payload.IsValid())
    {
        LastError = TEXT("Failed to parse Knoema response JSON.");
        return;
    }

    LastStatus.SimulationId = Payload->GetStringField(TEXT("simulation_id"));
    LastStatus.Status = Payload->GetStringField(TEXT("status"));
    LastStatus.CompletedTicks = Payload->GetIntegerField(TEXT("completed_ticks"));
    LastStatus.TotalTicks = Payload->GetIntegerField(TEXT("total_ticks"));
    if (Payload->HasTypedField<EJson::String>(TEXT("error")))
    {
        LastStatus.Error = Payload->GetStringField(TEXT("error"));
    }
    else
    {
        LastStatus.Error = FString();
    }
}

FString UKnoemaClient::NormalizeBaseUrl(const FString& InBaseUrl)
{
    FString Normalized = InBaseUrl;
    if (Normalized.IsEmpty())
    {
        return TEXT("http://127.0.0.1:8000");
    }

    while (Normalized.EndsWith(TEXT("/")))
    {
        Normalized.LeftChopInline(1, false);
    }
    return Normalized;
}
