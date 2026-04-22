// swift-tools-version: 5.9

import PackageDescription

let package = Package(
    name: "LuvoireMobile",
    platforms: [
        .iOS(.v16),
        .macOS(.v13)
    ],
    products: [
        .library(name: "LuvoireMobile", targets: ["LuvoireMobile"])
    ],
    targets: [
        .target(name: "LuvoireMobile"),
        .testTarget(name: "LuvoireMobileTests", dependencies: ["LuvoireMobile"])
    ]
)
