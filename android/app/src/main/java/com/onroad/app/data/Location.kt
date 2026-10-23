package com.onroad.app.data

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationManager
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.ContextCompat
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.resume

/** A fresh fix from the phone (network first, then GPS), falling back to the last known one. No Play Services needed. */
@SuppressLint("MissingPermission")
suspend fun currentLocation(ctx: Context): Location? {
    val ok = ContextCompat.checkSelfPermission(ctx, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED ||
        ContextCompat.checkSelfPermission(ctx, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
    if (!ok) return null
    val lm = ctx.getSystemService(LocationManager::class.java)
    val providers = listOf(LocationManager.NETWORK_PROVIDER, LocationManager.GPS_PROVIDER, LocationManager.PASSIVE_PROVIDER)
        .filter { runCatching { lm.isProviderEnabled(it) }.getOrDefault(false) }
    val recent = providers.mapNotNull { runCatching { lm.getLastKnownLocation(it) }.getOrNull() }.maxByOrNull { it.time }
    if (recent != null && System.currentTimeMillis() - recent.time < 10 * 60_000) return recent
    if (Build.VERSION.SDK_INT >= 30) {
        for (p in providers.filter { it != LocationManager.PASSIVE_PROVIDER }) {
            val fix = withTimeoutOrNull(if (p == LocationManager.NETWORK_PROVIDER) 6_000L else 10_000L) {
                suspendCancellableCoroutine<Location?> { cont ->
                    lm.getCurrentLocation(p, null, ctx.mainExecutor) { cont.resume(it) }
                }
            }
            if (fix != null) return fix
        }
    }
    return recent
}

fun kmBetween(a1: Double, o1: Double, a2: Double, o2: Double): Double {
    val p = Math.PI / 180
    val h = 0.5 - Math.cos((a2 - a1) * p) / 2 + Math.cos(a1 * p) * Math.cos(a2 * p) * (1 - Math.cos((o2 - o1) * p)) / 2
    return 12742 * Math.asin(Math.sqrt(h))
}

/** Returns a function that asks for location permission (if needed), gets a fix, stores it, and reports it (null = failed). */
@Composable
fun rememberLocator(prefs: Prefs, onResult: (Location?) -> Unit): () -> Unit {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    val fetch: () -> Unit = {
        scope.launch {
            val loc = currentLocation(ctx)
            if (loc != null) { prefs.lat = loc.latitude; prefs.lng = loc.longitude }
            onResult(loc)
        }
    }
    val ask = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { r ->
        if (r.values.any { it }) fetch() else onResult(null)
    }
    return {
        if (ContextCompat.checkSelfPermission(ctx, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED) fetch()
        else ask.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION))
    }
}
