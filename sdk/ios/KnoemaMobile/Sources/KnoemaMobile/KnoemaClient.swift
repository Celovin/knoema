import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

public struct NPCActionResponse: Codable, Equatable, Sendable {
    public let agentId: String
    public let actionType: String
    public let content: String
    public let isOffline: Bool

    public init(agentId: String, actionType: String, content: String, isOffline: Bool = false) {
        self.agentId = agentId
        self.actionType = actionType
        self.content = content
        self.isOffline = isOffline
    }
}

public struct AgentSnapshot: Codable, Equatable, Sendable {
    public let agentId: String
    public let displayName: String
    public let location: String
    public let summary: String

    public init(agentId: String, displayName: String, location: String, summary: String) {
        self.agentId = agentId
        self.displayName = displayName
        self.location = location
        self.summary = summary
    }
}

public final class KnoemaClient: @unchecked Sendable {
    public let baseURL: URL
    public let token: String?
    private var responseCache: [String: NPCActionResponse]

    public init(baseURL: URL, token: String? = nil) {
        self.baseURL = baseURL
        self.token = token
        self.responseCache = [:]
    }

    public func buildRESTRequest(path: String, method: String = "GET") -> URLRequest {
        let url = baseURL.appending(path: path.trimmingCharacters(in: CharacterSet(charactersIn: "/")))
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "accept")
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "authorization")
        }
        return request
    }

    public func buildWebSocketURL(path: String = "/ws/simulations/default") -> URL {
        var components = URLComponents(url: baseURL, resolvingAgainstBaseURL: false)!
        components.scheme = baseURL.scheme == "https" ? "wss" : "ws"
        components.path = path
        return components.url!
    }

    public func cache(response: NPCActionResponse, for key: String) {
        responseCache[key] = response
    }

    public func cachedResponse(for key: String) -> NPCActionResponse? {
        responseCache[key]
    }

    public func offlineResponse(agentId: String, input: String) -> NPCActionResponse {
        NPCActionResponse(
            agentId: agentId,
            actionType: "speak",
            content: "Offline response for \(input)",
            isOffline: true
        )
    }
}
