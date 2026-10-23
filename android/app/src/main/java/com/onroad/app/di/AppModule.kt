package com.onroad.app.di

import com.onroad.app.data.Api
import com.onroad.app.data.Prefs
import com.onroad.app.data.ServerInterceptor
import com.onroad.app.data.SessionCookies
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonNamingStrategy
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @OptIn(ExperimentalSerializationApi::class)
    @Provides @Singleton
    fun json() = Json { ignoreUnknownKeys = true; coerceInputValues = true; explicitNulls = false; namingStrategy = JsonNamingStrategy.SnakeCase }

    @Provides @Singleton
    fun client(prefs: Prefs): OkHttpClient = OkHttpClient.Builder().addInterceptor(ServerInterceptor(prefs)).cookieJar(SessionCookies(prefs))
        .apply { if (com.onroad.app.BuildConfig.DEBUG) addInterceptor(okhttp3.logging.HttpLoggingInterceptor().setLevel(okhttp3.logging.HttpLoggingInterceptor.Level.BASIC)) }
        .connectTimeout(20, TimeUnit.SECONDS).readTimeout(60, TimeUnit.SECONDS).build()

    @Provides @Singleton
    fun api(client: OkHttpClient, json: Json): Api = Retrofit.Builder().baseUrl("http://placeholder.invalid/").client(client)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType())).build().create(Api::class.java)
}
