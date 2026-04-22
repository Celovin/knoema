// swift-tools-version: 5.9

import PackageDescription

let package = Package(
    name: "KnoemaMobile",
    platforms: [
        .iOS(.v16),
        .macOS(.v13)
    ],
    products: [
        .library(name: "KnoemaMobile", targets: ["KnoemaMobile"])
    ],
    targets: [
        .target(name: "KnoemaMobile"),
        .testTarget(name: "KnoemaMobileTests", dependencies: ["KnoemaMobile"])
    ]
)
