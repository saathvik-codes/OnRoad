package com.onroad.app.ui

import android.graphics.drawable.GradientDrawable
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.onroad.app.data.NearDealer
import org.osmdroid.config.Configuration
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.BoundingBox
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.CustomZoomButtonsController
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker

/**
 * Pan / pinch-zoom map of the listed places (OpenStreetMap tiles, no API key). Tapping a pin opens a card with the
 * verified phone and directions; the map fits all pins plus the buyer's position on first show.
 */
@Composable
fun PlacesMap(places: List<NearDealer>, here: Pair<Double, Double>?, call: (NearDealer) -> Unit, go: (NearDealer) -> Unit,
              modifier: Modifier = Modifier) {
    val ctx = LocalContext.current
    var picked by remember(places) { mutableStateOf(places.firstOrNull()) }
    val pinColor = Ignition.toArgb(); val meColor = Electric.toArgb()
    val map = remember {
        Configuration.getInstance().userAgentValue = ctx.packageName           // OSM tile policy: identify the app
        MapView(ctx).apply {
            setTileSource(TileSourceFactory.MAPNIK)
            setMultiTouchControls(true)
            zoomController.setVisibility(CustomZoomButtonsController.Visibility.NEVER)
            isTilesScaledToDpi = true
            minZoomLevel = 5.0
            // a drag on the map pans the map; without this the surrounding list steals vertical swipes
            setOnTouchListener { v, e ->
                v.parent?.requestDisallowInterceptTouchEvent(e.actionMasked != android.view.MotionEvent.ACTION_UP && e.actionMasked != android.view.MotionEvent.ACTION_CANCEL)
                false
            }
        }
    }
    DisposableEffect(Unit) { map.onResume(); onDispose { map.onPause(); map.onDetach() } }
    Box(modifier) {
        AndroidView({ map }, Modifier.fillMaxWidth().height(420.dp).clip(Corner)) { m ->
            m.overlays.clear()
            fun dot(color: Int, size: Int) = GradientDrawable().apply {
                shape = GradientDrawable.OVAL; setColor(color); setStroke(4, android.graphics.Color.WHITE); setSize(size, size)
            }
            here?.let { (la, lo) ->
                m.overlays.add(Marker(m).apply { position = GeoPoint(la, lo); icon = dot(meColor, 40); title = "You"
                    setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER); setOnMarkerClickListener { _, _ -> true } })
            }
            val pts = places.filter { it.lat != null && it.lng != null }
            pts.forEach { d ->
                m.overlays.add(Marker(m).apply {
                    position = GeoPoint(d.lat!!, d.lng!!); icon = dot(pinColor, if (d == picked) 64 else 44)
                    setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER)
                    setOnMarkerClickListener { _, _ -> picked = d; m.controller.animateTo(position); true }
                })
            }
            if (m.tag != places) {                                              // fit once per result set, not on every tap
                m.tag = places
                val all = pts.map { GeoPoint(it.lat!!, it.lng!!) } + listOfNotNull(here?.let { GeoPoint(it.first, it.second) })
                if (all.size >= 2) m.post { m.zoomToBoundingBox(BoundingBox.fromGeoPoints(all).increaseByScale(1.25f), false, 48) }
                else all.firstOrNull()?.let { m.controller.setZoom(14.0); m.controller.setCenter(it) }
            }
            m.invalidate()
        }
        Text("© OpenStreetMap contributors", color = Mute, style = MaterialTheme.typography.labelSmall,
            modifier = Modifier.align(Alignment.BottomEnd).padding(6.dp).clip(Corner).background(Panel.copy(alpha = 0.85f)).padding(horizontal = 6.dp, vertical = 2.dp))
    }
    picked?.let { d ->
        Column(Modifier.fillMaxWidth().padding(top = 10.dp).clip(Corner).background(Panel2).padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(d.name, fontWeight = FontWeight.SemiBold, maxLines = 2, overflow = TextOverflow.Ellipsis)
            Text(listOfNotNull(d.distanceKm?.let { "$it km" }, d.googleRating?.let { "★ $it (${d.googleCount ?: 0})" },
                d.openNow?.let { if (it) "Open now" else "Closed now" }).joinToString(" · "), color = Mute, style = MaterialTheme.typography.bodySmall)
            if (d.address.isNotBlank()) Text(d.address, color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 2, overflow = TextOverflow.Ellipsis)
            val phones = d.phone?.split(',', ';', '/')?.map { it.trim() }?.filter { it.isNotEmpty() }.orEmpty()
            phones.firstOrNull()?.let { Text(it + if (d.phoneVerified) "  ·  verified" else "", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Medium) }
            if (phones.size > 1) Text("Other lines: " + phones.drop(1).joinToString(", "), color = Mute, style = MaterialTheme.typography.bodySmall)
            d.altPhone?.let { Text("Also listed on Google: $it", color = Mute, style = MaterialTheme.typography.bodySmall) }
            Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                if (d.phone != null) Text("Call", color = Good, fontWeight = FontWeight.SemiBold, modifier = Modifier.clickableText { call(d) })
                Text("Directions", color = Ignition, fontWeight = FontWeight.SemiBold, modifier = Modifier.clickableText { go(d) })
            }
        }
    }
}

private fun Modifier.clickableText(onClick: () -> Unit) = this.clickable(onClick = onClick).padding(vertical = 6.dp)
