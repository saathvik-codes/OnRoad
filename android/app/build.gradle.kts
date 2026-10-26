import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
    alias(libs.plugins.google.services)
    alias(libs.plugins.crashlytics)
    alias(libs.plugins.app.distribution)
}

android {
    namespace = "com.onroad.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.onroad.app"
        minSdk = 26
        targetSdk = 36
        versionCode = 4
        versionName = "1.0.2"
        // Same API as the OnRoad website. Change it in Settings (tunnel / server URL).
        buildConfigField("String", "DEFAULT_SERVER", "\"http://10.0.2.2:8101\"")      // local API, reachable only from the emulator
        buildConfigField("String", "LIVE_SERVER", "\"https://onroad-uu9c.onrender.com\"")
        // AdMob: Google's public test IDs unless android/ads.properties (git-ignored) has the real ones
        val ads = Properties().apply { val f = rootProject.file("ads.properties"); if (f.exists()) f.inputStream().use { load(it) } }
        manifestPlaceholders["admobAppId"] = ads.getProperty("ADMOB_APP_ID") ?: "ca-app-pub-3940256099942544~3347511713"
        buildConfigField("String", "BANNER_AD", "\"${ads.getProperty("ADMOB_BANNER") ?: "ca-app-pub-3940256099942544/9214589741"}\"")
        buildConfigField("boolean", "ADS_ON", "true")
    }
    // Release signing: the upload key lives outside the repo (D:/dev/keys); its passwords are in the git-ignored
    // android/keystore.properties. Without that file (e.g. CI), release falls back to the debug key.
    val keyProps = Properties().apply {
        val f = rootProject.file("keystore.properties"); if (f.exists()) f.inputStream().use { load(it) }
    }
    signingConfigs {
        if (keyProps.getProperty("storeFile") != null) create("upload") {
            storeFile = file(keyProps.getProperty("storeFile"))
            storePassword = keyProps.getProperty("storePassword")
            keyAlias = keyProps.getProperty("keyAlias")
            keyPassword = keyProps.getProperty("keyPassword")
        }
    }

    buildTypes {
        debug {
            // Google's test banner: a developer's own phone must never request (or click) real ads
            buildConfigField("String", "BANNER_AD", "\"ca-app-pub-3940256099942544/9214589741\"")
        }
        release {
            // ./gradlew assembleRelease appDistributionUploadRelease  (key file stays outside git; needs the
            // "Firebase App Distribution Admin" role on that service account)
            firebaseAppDistribution {
                artifactType = "APK"
                serviceCredentialsFile = rootProject.file("../onroad-6c950-firebase-adminsdk-fbsvc-78d608a81d.json").path
                testersFile = rootProject.file("../firebase/testers.txt").path      // one email per line
                groups = "internal-testers"
                releaseNotes = "OnRoad test build"
            }
            // production API on Render (also editable in Profile → Server)
            buildConfigField("String", "DEFAULT_SERVER", "\"https://onroad-uu9c.onrender.com\"")
            // release shows ads only with real AdMob IDs (never test ads to real users)
            val ads = Properties().apply { val f = rootProject.file("ads.properties"); if (f.exists()) f.inputStream().use { load(it) } }
            buildConfigField("boolean", "ADS_ON", (ads.getProperty("ADMOB_BANNER") != null).toString())
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfig = signingConfigs.findByName("upload") ?: signingConfigs.getByName("debug")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures { compose = true; buildConfig = true }
}

kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.splashscreen)
    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.compose.material3)
    implementation(libs.compose.material.icons)
    debugImplementation(libs.compose.ui.tooling)
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
    implementation(libs.androidx.hilt.navigation.compose)
    implementation(libs.retrofit)
    implementation(libs.retrofit.serialization)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.androidx.datastore)
    implementation(libs.coil.compose)
    implementation(libs.coil.okhttp)
    implementation(libs.coil.svg)
    implementation(libs.androidx.work)
    implementation(libs.androidx.browser)
    implementation(libs.play.services.location)
    implementation(libs.androidx.credentials)
    implementation(libs.androidx.credentials.play)
    implementation(libs.googleid)
    implementation(platform(libs.firebase.bom))
    implementation(libs.firebase.analytics)
    implementation(libs.play.ads)
    implementation(libs.ump)
    implementation(libs.firebase.crashlytics)
    implementation(libs.firebase.messaging)
    implementation(libs.kotlinx.coroutines.play.services)
}
