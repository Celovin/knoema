import Foundation
import XCTest
@testable import KnoemaMobile

final class KnoemaMobileTests: XCTestCase {
    func testBuildsAuthorizedRESTRequest() throws {
        let client = KnoemaClient(baseURL: URL(string: "https://api.example.test")!, token: "demo")
        let request = client.buildRESTRequest(path: "/agents/alice", method: "POST")

        XCTAssertEqual(request.url?.absoluteString, "https://api.example.test/agents/alice")
        XCTAssertEqual(request.httpMethod, "POST")
        XCTAssertEqual(request.value(forHTTPHeaderField: "authorization"), "Bearer demo")
    }

    func testBuildsWebSocketURL() throws {
        let client = KnoemaClient(baseURL: URL(string: "https://api.example.test")!)

        XCTAssertEqual(
            client.buildWebSocketURL(path: "/ws/simulations/demo").absoluteString,
            "wss://api.example.test/ws/simulations/demo"
        )
    }

    func testNpcAgentCachesOfflineResponse() throws {
        let client = KnoemaClient(baseURL: URL(string: "http://localhost:8000")!)
        let agent = NPCAgent(agentId: "alice", displayName: "Alice", client: client)

        let first = agent.cachedOrOfflineResponse(input: "hello")
        let second = agent.cachedOrOfflineResponse(input: "hello")

        XCTAssertTrue(first.isOffline)
        XCTAssertEqual(first, second)
    }
}
