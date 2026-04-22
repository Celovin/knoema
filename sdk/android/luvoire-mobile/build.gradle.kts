plugins {
    id("com.android.library")
    kotlin("android")
}

android {
    namespace = "com.celovin.luvoire"
    compileSdk = 35

    defaultConfig {
        minSdk = 26
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
}
