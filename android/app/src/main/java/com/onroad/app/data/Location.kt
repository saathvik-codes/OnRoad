package com.onroad.app.data

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationManager
import android.os.Build
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.ContextCompat
import androidx.core.location.LocationManagerCompat
import com.google.android.gms.common.ConnectionResult
import com.google.android.gms.common.GoogleApiAvailability
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.resume

/** Why a location request failed, in words a user can act on. */
enum class LocationProblem(val message: String) {
    Denied("Location permission is off for OnRoad. Allow it in Settings, or pick your city."),
    Off("Your phone's location is turned off. Turn it on, or pick your city."),
    NoFix("Couldn't get a location fix yet. Step near a window and try again, or pick your city."),
}

private fun hasPermission(ctx: Context) =
    ContextCompat.checkSelfPermission(ctx, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED ||
        ContextCompat.checkSelfPermission(ctx, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED

/**
 * A current location: Google Play's fused provider first (what Maps uses: Wi-Fi + cell + GPS), then Android's own
 * providers as a fallback for phones without Play services. A fix from the last 10 minutes is used straight away.
 */
@SuppressLint("MissingPermission")
suspend fun currentLocation(ctx: Context): Pair<Location?, LocationProblem?> {
    if (!hasPermission(ctx)) return null to LocationProblem.Denied
    val lm = ctx.getSystemService(LocationManager::class.java)
    if (!LocationManagerCompat.isLocationEnabled(lm)) return null to LocationProblem.Off
    val fresh = { l: Location? -> l != null && System.currentTimeMillis() - l.time < 10 * 60_000 }

    if (GoogleApiAvailability.getInstance().isGooglePlayServicesAvailable(ctx) == ConnectionResult.SUCCESS) {
        val fused = LocationServices.getFusedLocationProviderClient(ctx)
        runCatching { fused.lastLocation.await() }.getOrNull()?.let { if (fresh(it)) return it to null }
        for ((priority, wait) in listOf(Priority.PRIORITY_BALANCED_POWER_ACCURACY to 12_000L, Priority.PRIORITY_HIGH_ACCURACY to 20_000L)) {
            val cts = CancellationTokenSource()
            val fix = withTimeoutOrNull(wait) { runCatching { fused.getCurrentLocation(priority, cts.token).await() }.getOrNull() }
            cts.cancel()
            if (fix != null) return fix to null
        }
    }

    // fallback: platform providers
    val providers = listOf(LocationManager.NETWORK_PROVIDER, LocationManager.GPS_PROVIDER)
        .filter { runCatching { lm.isProviderEnabled(it) }.getOrDefault(false) }
    val last = (providers + LocationManager.PASSIVE_PROVIDER).mapNotNull { runCatching { lm.getLastKnownLocation(it) }.getOrNull() }.maxByOrNull { it.time }
    if (fresh(last)) return last to null
    if (Build.VERSION.SDK_INT >= 30) {
        for (p in providers) {
            val fix = withTimeoutOrNull(if (p == LocationManager.NETWORK_PROVIDER) 10_000L else 20_000L) {
                suspendCancellableCoroutine<Location?> { cont -> lm.getCurrentLocation(p, null, ctx.mainExecutor) { cont.resume(it) } }
            }
            if (fix != null) return fix to null
        }
    }
    return if (last != null) last to null else null to LocationProblem.NoFix
}

fun kmBetween(a1: Double, o1: Double, a2: Double, o2: Double): Double {
    val p = Math.PI / 180
    val h = 0.5 - Math.cos((a2 - a1) * p) / 2 + Math.cos(a1 * p) * Math.cos(a2 * p) * (1 - Math.cos((o2 - o1) * p)) / 2
    return 12742 * Math.asin(Math.sqrt(h))
}

/** Opens the phone's location settings (for the "location is off" case). */
fun openLocationSettings(ctx: Context) =
    ctx.startActivity(Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))

/**
 * Returns a function that asks for location permission when needed, gets a fix, stores it, and reports the result:
 * the location, or the reason it failed.
 */
@Composable
fun rememberLocator(prefs: Prefs, onResult: (Location?, LocationProblem?) -> Unit): () -> Unit {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    val fetch: () -> Unit = {
        scope.launch {
            val (loc, problem) = currentLocation(ctx)
            if (loc != null) { prefs.lat = loc.latitude; prefs.lng = loc.longitude }
            onResult(loc, problem)
        }
    }
    val ask = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { r ->
        if (r.values.any { it }) fetch() else onResult(null, LocationProblem.Denied)
    }
    return {
        if (hasPermission(ctx)) fetch()
        else ask.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION))
    }
}
