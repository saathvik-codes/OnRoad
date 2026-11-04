package com.onroad.app.ui

import android.app.Activity
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.google.android.gms.ads.AdListener
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.AdSize
import com.google.android.gms.ads.AdView
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.MobileAds
import com.google.android.ump.ConsentRequestParameters
import com.google.android.ump.UserMessagingPlatform
import com.onroad.app.BuildConfig
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Google AdMob. Real IDs come from the git-ignored android/ads.properties; debug builds always use Google's test ads,
 * and a release without real IDs shows no ads at all. Consent (Google's UMP form) is asked first where the law needs
 * it; ads only load once it is settled.
 */
object Ads {
    private val started = AtomicBoolean(false)
    var ready by mutableStateOf(false)
        private set

    fun start(activity: Activity) {
        if (!BuildConfig.ADS_ON) return
        val consent = UserMessagingPlatform.getConsentInformation(activity)
        val go = {
            if (consent.canRequestAds() && started.compareAndSet(false, true)) {
                Thread { MobileAds.initialize(activity) { activity.runOnUiThread { ready = true } } }.start()
            }
        }
        consent.requestConsentInfoUpdate(activity, ConsentRequestParameters.Builder().build(), {
            UserMessagingPlatform.loadAndShowConsentFormIfRequired(activity) { go() }
        }, { go() })
        go()    // consent from an earlier launch is enough to start straight away
    }

    // Full-screen ads, kept rare: an interstitial only at a natural break (every 4th car opened), and an app-open ad only
    // when someone comes back to the app after a while. Never more than one full-screen ad every 4 minutes.
    private var interstitial: com.google.android.gms.ads.interstitial.InterstitialAd? = null
    private var appOpen: com.google.android.gms.ads.appopen.AppOpenAd? = null
    private var lastFull = 0L
    private var lastAppOpen = 0L
    private var carsOpened = 0
    private const val GAP_MS = 4 * 60_000L

    private fun loadInterstitial(a: Activity) {
        if (!BuildConfig.ADS_ON || !ready || interstitial != null) return
        com.google.android.gms.ads.interstitial.InterstitialAd.load(a, BuildConfig.INTERSTITIAL_AD, AdRequest.Builder().build(),
            object : com.google.android.gms.ads.interstitial.InterstitialAdLoadCallback() {
                override fun onAdLoaded(ad: com.google.android.gms.ads.interstitial.InterstitialAd) { interstitial = ad }
            })
    }

    private fun loadAppOpen(a: Activity) {
        if (!BuildConfig.ADS_ON || !ready || appOpen != null) return
        com.google.android.gms.ads.appopen.AppOpenAd.load(a, BuildConfig.APP_OPEN_AD, AdRequest.Builder().build(),
            object : com.google.android.gms.ads.appopen.AppOpenAd.AppOpenAdLoadCallback() {
                override fun onAdLoaded(ad: com.google.android.gms.ads.appopen.AppOpenAd) { appOpen = ad }
            })
    }

    /** Call when a car page opens. */
    fun onCarOpened(a: Activity) {
        carsOpened++
        val ad = interstitial
        if (ad != null && carsOpened % 4 == 0 && System.currentTimeMillis() - lastFull > GAP_MS) {
            interstitial = null; lastFull = System.currentTimeMillis()
            ad.show(a)
        }
        loadInterstitial(a)
    }

    /** Call from the activity's onStart; [awayMs] is how long the app was in the background. */
    fun onReturn(a: Activity, awayMs: Long) {
        val now = System.currentTimeMillis()
        val ad = appOpen
        if (ad != null && awayMs > 60_000 && now - lastFull > GAP_MS && now - lastAppOpen > 3 * 3_600_000L) {
            appOpen = null; lastFull = now; lastAppOpen = now
            ad.show(a)
        }
        loadAppOpen(a); loadInterstitial(a)
    }
}

/** A native ad laid out like one of our cards (icon, headline, text, picture, button), labelled Sponsored. */
@Composable
fun AdNative(modifier: Modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)) {
    if (!BuildConfig.ADS_ON || !Ads.ready) return
    var ad by remember { mutableStateOf<com.google.android.gms.ads.nativead.NativeAd?>(null) }
    val ctx = androidx.compose.ui.platform.LocalContext.current
    androidx.compose.runtime.DisposableEffect(Unit) {
        com.google.android.gms.ads.AdLoader.Builder(ctx, BuildConfig.NATIVE_AD).forNativeAd { ad = it }.build()
            .loadAd(AdRequest.Builder().build())
        onDispose { ad?.destroy() }
    }
    val n = ad ?: return
    val ink = Ink.toArgb(); val mute = Mute.toArgb(); val accent = Ignition.toArgb(); val panel = Panel.toArgb()
    AndroidView(modifier = modifier.fillMaxWidth(), factory = { c ->
        val dp = c.resources.displayMetrics.density
        val view = com.google.android.gms.ads.nativead.NativeAdView(c)
        val col = android.widget.LinearLayout(c).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding((14 * dp).toInt(), (12 * dp).toInt(), (14 * dp).toInt(), (14 * dp).toInt())
            background = android.graphics.drawable.GradientDrawable().apply { setColor(panel); cornerRadius = 16 * dp }
        }
        val label = android.widget.TextView(c).apply { text = "Sponsored"; textSize = 11f; setTextColor(mute) }
        val row = android.widget.LinearLayout(c).apply { gravity = android.view.Gravity.CENTER_VERTICAL; setPadding(0, (6 * dp).toInt(), 0, (8 * dp).toInt()) }
        val icon = android.widget.ImageView(c).apply { layoutParams = android.widget.LinearLayout.LayoutParams((40 * dp).toInt(), (40 * dp).toInt()).apply { marginEnd = (10 * dp).toInt() } }
        val headline = android.widget.TextView(c).apply { textSize = 15f; setTextColor(ink); setTypeface(typeface, android.graphics.Typeface.BOLD); maxLines = 2 }
        row.addView(icon); row.addView(headline, android.widget.LinearLayout.LayoutParams(0, -2, 1f))
        val media = com.google.android.gms.ads.nativead.MediaView(c).apply { layoutParams = android.widget.LinearLayout.LayoutParams(-1, (170 * dp).toInt()) }
        val body = android.widget.TextView(c).apply { textSize = 13f; setTextColor(mute); maxLines = 2; setPadding(0, (8 * dp).toInt(), 0, (10 * dp).toInt()) }
        val cta = android.widget.Button(c).apply {
            isAllCaps = false; setTextColor(android.graphics.Color.WHITE)
            background = android.graphics.drawable.GradientDrawable().apply { setColor(accent); cornerRadius = 12 * dp }
        }
        col.addView(label); col.addView(row); col.addView(media); col.addView(body); col.addView(cta, android.widget.LinearLayout.LayoutParams(-1, (44 * dp).toInt()))
        view.addView(col)
        view.headlineView = headline; view.bodyView = body; view.iconView = icon; view.mediaView = media; view.callToActionView = cta
        view
    }, update = { v ->
        (v.headlineView as android.widget.TextView).text = n.headline
        (v.bodyView as android.widget.TextView).apply { text = n.body; visibility = if (n.body.isNullOrBlank()) android.view.View.GONE else android.view.View.VISIBLE }
        (v.callToActionView as android.widget.Button).apply { text = n.callToAction ?: "Learn more"; visibility = if (n.callToAction == null) android.view.View.GONE else android.view.View.VISIBLE }
        (v.iconView as android.widget.ImageView).apply { setImageDrawable(n.icon?.drawable); visibility = if (n.icon == null) android.view.View.GONE else android.view.View.VISIBLE }
        v.mediaView?.mediaContent = n.mediaContent
        v.setNativeAd(n)
    })
}

/** One quiet banner, labelled, full width; takes no space until an ad has actually loaded. */
@Composable
fun AdBanner(modifier: Modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)) {
    if (!BuildConfig.ADS_ON || !Ads.ready) return
    val width = LocalConfiguration.current.screenWidthDp - 32
    var loaded by remember { mutableStateOf(false) }
    Column(modifier.fillMaxWidth()) {
        if (loaded) Text("Sponsored", color = Mute, style = MaterialTheme.typography.labelSmall, modifier = Modifier.padding(bottom = 4.dp))
        AndroidView(factory = { ctx ->
            AdView(ctx).apply {
                setAdSize(AdSize.getLargeAnchoredAdaptiveBannerAdSize(ctx, width))
                adUnitId = BuildConfig.BANNER_AD
                adListener = object : AdListener() {
                    override fun onAdLoaded() { loaded = true }
                    override fun onAdFailedToLoad(e: LoadAdError) { loaded = false }
                }
                loadAd(AdRequest.Builder().build())
            }
        }, modifier = Modifier.fillMaxWidth(), onRelease = { it.destroy() })
    }
}
