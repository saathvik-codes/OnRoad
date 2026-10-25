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
        .addInterceptor(WakeRetry())
        .connectTimeout(45, TimeUnit.SECONDS).readTimeout(90, TimeUnit.SECONDS).build()

    @Provides @Singleton
    fun api(client: OkHttpClient, json: Json): Api = Retrofit.Builder().baseUrl("http://placeholder.invalid/").client(client)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType())).build().create(Api::class.java)
}


/** The API sleeps when idle (free hosting) and answers slowly or with 502-504 while waking: retry reads a few times. */
class WakeRetry : okhttp3.Interceptor {
    override fun intercept(chain: okhttp3.Interceptor.Chain): okhttp3.Response {
        val req = chain.request()
        if (req.method != "GET") return chain.proceed(req)
        var wait = 3000L
        repeat(3) {
            try {
                val r = chain.proceed(req)
                if (r.code !in 502..504) return r
                r.close()
            } catch (e: java.io.IOException) {
                if (e is java.io.InterruptedIOException && e !is java.net.SocketTimeoutException) throw e   // cancelled
            }
            Thread.sleep(wait); wait *= 2
        }
        return chain.proceed(req)
    }
}
