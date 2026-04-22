using UnrealBuildTool;

public class LuvoireUnreal : ModuleRules
{
    public LuvoireUnreal(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        CppStandard = CppStandardVersion.Cpp20;

        PublicDependencyModuleNames.AddRange(
            new[]
            {
                "Core",
                "CoreUObject",
                "Engine",
                "HTTP",
                "Json",
                "JsonUtilities"
            }
        );

        PrivateDependencyModuleNames.AddRange(
            new[]
            {
                "Projects"
            }
        );
    }
}
