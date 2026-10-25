package com.onroad.app.data

import android.content.Context
import com.onroad.app.BuildConfig
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.Serializable
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.Interceptor
import okhttp3.Response
import okhttp3.Cookie
import okhttp3.CookieJar
import okhttp3.HttpUrl
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query
import java.net.URLEncoder
import javax.inject.Inject
import javax.inject.Singleton

// ── DTOs: mirror the OnRoad API (backend/onroad/api.py). JSON is snake_case; the Json instance maps it. ──

@Serializable data class Brand(val slug: String, val name: String, val logo: String? = null, val models: Int = 0,
    val fromInr: Long? = null, val dealersHere: Int = 0, val offers: Int = 0, val vehicleType: String? = null)

@Serializable data class ModelSummary(val id: String, val name: String, val brand: String = "", val brandSlug: String = "",
    val bodyType: String? = null, val imageUrl: String? = null, val fromInr: Long? = null, val toInr: Long? = null,
    val fuels: String? = null, val variants: Int = 0, val offers: Int = 0, val salesRank: Int? = null,
    val transmissions: String? = null, val band: String? = null)

@Serializable data class Line(val label: String, val amountInr: Long? = null, val basis: String = "", val source: kotlinx.serialization.json.JsonElement? = null,
    val verified: Boolean = true, val optional: Boolean = false, val refundable: Boolean = false)

@Serializable data class Breakdown(val stateName: String = "", val coverage: String = "", val exShowroomInr: Long = 0,
    val lines: List<Line> = emptyList(), val totalInr: Long = 0, val refundableInr: Long = 0, val priceCity: String? = null)

@Serializable data class Variant(val id: String, val name: String, val fuel: String? = null, val transmission: String? = null,
    val engineCc: Int? = null, val batteryKwh: Double? = null, val seats: Int? = null, val exShowroomInr: Long? = null,
    val priceCity: String? = null, val priceSource: String? = null, val onroad: Breakdown? = null, val imageUrl: String? = null)

@Serializable data class Dealer(val id: String, val name: String, val address: String = "", val phone: String? = null,
    val lat: Double? = null, val lng: Double? = null, val kind: String = "", val distanceKm: Double? = null, val city: String? = null,
    val onroadRating: Double? = null, val onroadCount: Int = 0, val googleRating: Double? = null, val googleCount: Int? = null)

@Serializable data class Offer(val title: String, val amountInr: Long? = null, val details: String = "", val validUntil: String? = null,
    val kind: String? = null, val conditions: String? = null, val sourceUrl: String? = null)

@Serializable data class CrashTest(val agency: String, val protocol: String = "", val adultStars: Int? = null, val childStars: Int? = null,
    val adultScore: Double? = null, val adultMax: Double? = null, val childScore: Double? = null, val childMax: Double? = null,
    val sourceUrl: String = "", val videoUrl: String? = null, val ratingPublished: String? = null)

@Serializable data class ModelDetail(val id: String, val name: String, val brandName: String = "", val brandSlug: String = "",
    val bodyType: String? = null, val imageUrl: String? = null, val logo: String? = null, val url: String? = null,
    val variants: List<Variant> = emptyList(), val dealers: List<Dealer> = emptyList(), val offers: List<Offer> = emptyList(),
    val crashTests: List<CrashTest> = emptyList(), val gallery: List<GalleryItem> = emptyList(), val vehicleType: String? = null,
    val priceHistory: List<PricePoint> = emptyList(),
    val brandVehicleType: String? = null)
@Serializable data class GalleryItem(val url: String, val label: String = "", val kind: String = "model")

@Serializable data class Spec(val grp: String, val key: String, val label: String, val value: String, val sourceUrl: String = "")
@Serializable data class Feature(val key: String, val label: String)
@Serializable data class Photo(val imageUrl: String)
@Serializable data class VariantSpecs(val specs: List<Spec> = emptyList(), val features: List<Feature> = emptyList(),
    val photos: Map<String, Photo> = emptyMap(), val modelUrl: String? = null)

@Serializable data class City(val name: String, val state: String, val stateName: String, val lat: Double, val lng: Double)
@Serializable data class Hit(val id: String, val name: String, val brand: String, val brandSlug: String, val fromInr: Long? = null, val note: String? = null)

@Serializable data class OfferItem(val id: Long = 0, val brandSlug: String = "", val modelName: String? = null, val title: String = "",
    val amountInr: Long? = null, val details: String = "", val validUntil: String? = null, val sourceUrl: String? = null,
    val brandName: String? = null, val modelImage: String? = null, val kind: String? = null, val conditions: String? = null)
@Serializable data class LoanRate(val bank: String, val product: String = "", val evOnly: Int = 0, val minPct: Double? = null,
    val maxPct: Double? = null, val sourceUrl: String = "")
@Serializable data class Reco(val id: String, val name: String, val brand: String = "", val brandSlug: String = "", val bodyType: String? = null,
    val imageUrl: String? = null, val fromInr: Long? = null, val matchScore: Int = 0, val reasons: List<String> = emptyList(),
    val variant: String? = null, val variantId: String? = null, val transmission: String? = null, val crashStars: Int? = null,
    val warnings: List<String> = emptyList(), val fuels: String? = null, val pool: Int = 0, val efficiency: Double? = null)
@Serializable data class PricePoint(val variantId: String, val city: String, val exShowroomInr: Long, val fetchedAt: String)
@Serializable data class SaveIn(val variantId: String, val city: String, val targetInr: Long? = null)
@Serializable data class SavedCar(val variantId: String, val variant: String = "", val model: String = "", val modelId: String = "",
    val brand: String = "", val imageUrl: String? = null, val city: String = "")
@Serializable data class QuoteRequestIn(val variantId: String, val city: String, val pincode: String? = null, val finance: Boolean = false,
    val exchange: Boolean = false, val purchaseBy: String? = null, val note: String? = null, val consent: Boolean = true)
@Serializable data class Ok(val ok: Boolean = true)
@Serializable data class NearDealer(val id: String, val brandSlug: String = "", val brandName: String = "", val name: String = "",
    val address: String = "", val city: String? = null, val phone: String? = null, val lat: Double? = null, val lng: Double? = null,
    val kind: String = "", val distanceKm: Double? = null, val rating: Double? = null, val ratingCount: Int = 0,
    val googleRating: Double? = null, val googleCount: Int? = null, val googleMapsUri: String? = null, val photoUrl: String? = null,
    val photoCredit: String? = null, val website: String? = null)
@Serializable data class OwnReview(val rating: Int = 0, val priceHonesty: Int? = null, val noForcedAddons: Int? = null,
    val deliveryOnTime: Int? = null, val visit: String? = null, val text: String? = null, val created: String? = null, val name: String? = null)
@Serializable data class GReview(val author: String? = null, val rating: Int? = null,
    @kotlinx.serialization.SerialName("when") val whenText: String? = null, val text: String = "")
@Serializable data class GBlock(val rating: Double? = null, val count: Int? = null, val mapsUri: String? = null,
    val reviews: List<GReview> = emptyList(), val note: String? = null)
@Serializable data class DealerReviews(val onroad: List<OwnReview> = emptyList(), val google: GBlock? = null)
@Serializable data class DealerReviewIn(val dealerId: String, val rating: Int, val priceHonesty: Int? = null, val noForcedAddons: Boolean? = null,
    val deliveryOnTime: Boolean? = null, val visit: String = "purchase", val text: String = "")
@Serializable data class Band(val id: String, val label: String, val hint: String = "", val min: Long? = null, val max: Long? = null)
@Serializable data class DealerQuote(val dealer: String = "", val onRoadInr: Long? = null, val discountInr: Long? = null,
    val waitingWeeks: Int? = null, val validUntil: String? = null, val note: String? = null, val phone: String? = null)
@Serializable data class MyRequest(val id: Long, val variant: String = "", val model: String = "", val brand: String = "", val city: String = "",
    val status: String = "open", val created: String = "", val quotes: List<DealerQuote> = emptyList())

@Serializable data class LoginIn(val email: String, val password: String)
@Serializable data class GoogleIn(val idToken: String)
@Serializable data class GoogleConfig(val clientId: String? = null)
@Serializable data class SignupIn(val name: String, val email: String, val phone: String? = null, val password: String, val role: String = "buyer")
@Serializable data class Account(val id: Long = 0, val email: String = "", val name: String = "", val phone: String? = null, val role: String = "buyer")

interface Api {
    @POST("api/auth/login") suspend fun login(@Body body: LoginIn): Account
    @POST("api/auth/google") suspend fun google(@Body body: GoogleIn): Account
    @POST("api/me/push-token") suspend fun pushToken(@Body body: PushTokenIn): kotlinx.serialization.json.JsonObject
    @GET("api/auth/google/config") suspend fun googleConfig(): GoogleConfig
    @POST("api/auth/signup") suspend fun signup(@Body body: SignupIn): Account
    @POST("api/auth/logout") suspend fun logout()
    @GET("api/auth/me") suspend fun me(): Account
    @GET("api/offers") suspend fun offers(@Query("city") city: String, @Query("limit") limit: Int = 60): List<OfferItem>
    @GET("api/loan-rates") suspend fun loanRates(@Query("vehicle_type") type: String = "car"): List<LoanRate>
    @GET("api/recommendations") suspend fun recommendations(@Query("city") city: String, @Query("vehicle_type") type: String,
        @Query("budget") budget: Long, @Query("usage") usage: String, @Query("seats") seats: Int, @Query("fuel") fuel: String?,
        @Query("transmission") transmission: String?, @Query("monthly_km") monthlyKm: Int, @Query("priorities") priorities: String,
        @Query("limit") limit: Int = 8, @Query("body") body: String? = null, @Query("brands") brands: String? = null,
        @Query("budget_min") budgetMin: Long? = null): List<Reco>
    @GET("api/me/saved") suspend fun saved(): List<SavedCar>
    @POST("api/me/saved") suspend fun save(@Body body: SaveIn): Ok
    @POST("api/quotes/request") suspend fun requestQuote(@Body body: QuoteRequestIn): kotlinx.serialization.json.JsonObject
    @GET("api/brands") suspend fun brands(@Query("city") city: String, @Query("vehicle_type") type: String = "car"): List<Brand>
    @GET("api/explore") suspend fun explore(@Query("city") city: String, @Query("brand") brand: String? = null,
        @Query("band") band: String? = null, @Query("sort") sort: String = "popular",
        @Query("vehicle_type") type: String? = null, @Query("body") body: String? = null,
        @Query("fuel") fuel: String? = null, @Query("min_inr") minInr: Long? = null, @Query("max_inr") maxInr: Long? = null): List<ModelSummary>
    @GET("api/bands") suspend fun bands(): List<Band>
    @POST("api/dealer-reviews") suspend fun rateDealer(@Body body: DealerReviewIn): kotlinx.serialization.json.JsonObject
    @GET("api/dealer-reviews") suspend fun dealerReviews(@Query("dealer_id") dealerId: String): DealerReviews
    @GET("api/dealers/near") suspend fun dealersNear(@Query("lat") lat: Double, @Query("lng") lng: Double, @Query("brand") brand: String? = null,
        @Query("vehicle_type") type: String? = null, @Query("limit") limit: Int = 40): List<NearDealer>
    @GET("api/me/quotes") suspend fun myQuotes(): List<MyRequest>
    @retrofit2.http.DELETE("api/me/saved") suspend fun unsave(@Query("variant_id") variantId: String, @Query("city") city: String): Ok
    @GET("api/models/{brand}/{model}") suspend fun model(@Path("brand") brand: String, @Path("model") model: String,
        @Query("city") city: String, @Query("lat") lat: Double? = null, @Query("lng") lng: Double? = null): ModelDetail
    @GET("api/variant-specs") suspend fun specs(@Query("variant_id") id: String): VariantSpecs
    @GET("api/onroad/quick") suspend fun quick(@Query("ex_showroom") ex: Long, @Query("city") city: String,
        @Query("fuel") fuel: String, @Query("engine_cc") cc: Int?, @Query("vehicle_type") type: String = "car"): Breakdown
    @GET("api/cities") suspend fun cities(): List<City>
    @GET("api/search") suspend fun search(@Query("q") q: String): List<Hit>
}

/** Server URL + chosen city, kept in app-private prefs and exposed as flows. */
@Singleton
class Prefs @Inject constructor(@ApplicationContext ctx: Context) {
    private val sp = ctx.getSharedPreferences("onroad", Context.MODE_PRIVATE)
    private val _city = MutableStateFlow(sp.getString("city", "Hyderabad")!!)
    val city = _city.asStateFlow()
    fun setCity(c: String) { sp.edit().putString("city", c).apply(); _city.value = c }
    var onboarded: Boolean
        get() = sp.getBoolean("onboarded", false)
        set(v) { sp.edit().putBoolean("onboarded", v).apply() }
    /** The API's httpOnly session cookie ("or_session"), kept in app-private prefs so sign-in survives restarts. */
    var session: String?
        get() = sp.getString("session", null)
        set(v) { sp.edit().putString("session", v).apply() }
    private val _account = MutableStateFlow<Account?>(null)
    val account = _account.asStateFlow()
    fun setAccount(a: Account?) { _account.value = a }

    /** Ids already seen by the offers/new-model alert job (so each one notifies once). */
    var seenOffers: Set<String>
        get() = sp.getStringSet("seen_offers", emptySet())!!
        set(v) { sp.edit().putStringSet("seen_offers", v).apply() }
    var seenModels: Set<String>
        get() = sp.getStringSet("seen_models", emptySet())!!
        set(v) { sp.edit().putStringSet("seen_models", v).apply() }
    /** Phone's last coarse location (only when the user allowed it), for nearest showrooms and distances. */
    var lat: Double?
        get() = sp.getString("lat", null)?.toDoubleOrNull()
        set(v) { sp.edit().putString("lat", v?.toString()).apply() }
    var lng: Double?
        get() = sp.getString("lng", null)?.toDoubleOrNull()
        set(v) { sp.edit().putString("lng", v?.toString()).apply() }
    var askedNotify: Boolean
        get() = sp.getBoolean("asked_notify", false)
        set(v) { sp.edit().putBoolean("asked_notify", v).apply() }
    var alerts: Boolean
        get() = sp.getBoolean("alerts", true)
        set(v) { sp.edit().putBoolean("alerts", v).apply() }

    // release: always the live API. Debug: the local API on the emulator and the live
    // API on a real phone (10.0.2.2 only exists inside the emulator)
    fun server(): String = if (!BuildConfig.DEBUG) BuildConfig.DEFAULT_SERVER
        else if (onEmulator) BuildConfig.DEFAULT_SERVER else BuildConfig.LIVE_SERVER   // old saved test addresses are ignored

    private val onEmulator: Boolean by lazy {
        val b = android.os.Build.FINGERPRINT + android.os.Build.MODEL + android.os.Build.PRODUCT + android.os.Build.HARDWARE
        listOf("generic", "emulator", "sdk_gphone", "ranchu", "goldfish", "Android SDK built for").any { b.contains(it, ignoreCase = true) }
    }
    fun setServer(url: String) = sp.edit().putString("server", url.trim().trimEnd('/')).apply()

    /** Manufacturer images go through the API's resizing cache, exactly like the website. */
    fun img(url: String?, w: Int = 800): String? = url?.let {
        if (it.startsWith("http")) "${server()}/api/img?w=$w&u=${URLEncoder.encode(it, "UTF-8")}" else "${server()}$it"
    }
}

/** Points every request at the server chosen in Prefs (the API's host can change, e.g. a new tunnel). */
class ServerInterceptor(private val prefs: Prefs) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val req = chain.request()
        val base = prefs.server().toHttpUrlOrNull() ?: return chain.proceed(req)
        val url = req.url.newBuilder().scheme(base.scheme).host(base.host).port(base.port).build()
        return chain.proceed(req.newBuilder().url(url).build())
    }
}

/** Stores the API's session cookie and sends it back on every request to the OnRoad server. */
class SessionCookies(private val prefs: Prefs) : CookieJar {
    override fun saveFromResponse(url: HttpUrl, cookies: List<Cookie>) {
        cookies.firstOrNull { it.name == "or_session" }?.let { prefs.session = if (it.expiresAt < System.currentTimeMillis()) null else it.value }
    }
    override fun loadForRequest(url: HttpUrl): List<Cookie> =
        prefs.session?.let { listOf(Cookie.Builder().name("or_session").value(it).hostOnlyDomain(url.host).path("/").build()) } ?: emptyList()
}
