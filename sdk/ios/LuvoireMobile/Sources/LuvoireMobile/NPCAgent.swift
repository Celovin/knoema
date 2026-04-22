import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

public struct NPCAgent: Sendable {
    public let agentId: String
    public let displayName: String
    public let client: KnoemaClient

    public init(agentId: String, displayName: String, client: KnoemaClient) {
        self.agentId = agentId
        self.displayName = displayName
        self.client = client
    }

    public func cachedOrOfflineResponse(input: String) -> NPCActionResponse {
        let key = "\(agentId):\(input)"
        if let cached = client.cachedResponse(for: key) {
            return cached
        }
        let response = client.offlineResponse(agentId: agentId, input: input)
        client.cache(response: response, for: key)
        return response
    }

    public func agentEndpointRequest() -> URLRequest {
        client.buildRESTRequest(path: "/agents/\(agentId)", method: "GET")
    }
}
