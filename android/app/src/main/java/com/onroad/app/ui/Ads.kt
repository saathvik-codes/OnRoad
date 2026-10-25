package com.onroad.app.ui

import android.app.Activity
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
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
                setAdSize(AdSize.getCurrentOrientationAnchoredAdaptiveBannerAdSize(ctx, width))
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
