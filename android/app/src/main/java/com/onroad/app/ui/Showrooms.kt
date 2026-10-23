package com.onroad.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Call
import androidx.compose.material.icons.outlined.CloudOff
import androidx.compose.material.icons.outlined.Directions
import androidx.compose.material.icons.outlined.MyLocation
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.onroad.app.data.Brand
import com.onroad.app.data.NearDealer
import com.onroad.app.data.rememberLocator

/** Shown instead of an endless spinner when the server can't be reached. */
@Composable
fun ErrorState(message: String, onRetry: () -> Unit) = Column(
    Modifier.fillMaxWidth().padding(32.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(10.dp),
) {
    Icon(Icons.Outlined.CloudOff, null, tint = Mute, modifier = Modifier.size(40.dp))
    Text(message, color = Mute, textAlign = TextAlign.Center)
    Button(onRetry, colors = ButtonDefaults.buttonColors(containerColor = Panel2)) { Text("Try again", color = Ink) }
}

/** Nearest official showrooms of every brand (or one brand) by distance from the phone, with call and directions. */
@Composable
fun ShowroomsScreen(onBack: () -> Unit, vm: BrowseVM = hiltViewModel()) {
    val ctx = LocalContext.current
    var type by remember { mutableStateOf("car") }
    var brand by remember { mutableStateOf<String?>(null) }
    var brands by remember { mutableStateOf<List<Brand>>(emptyList()) }
    var list by remember { mutableStateOf<List<NearDealer>?>(null) }
    var err by remember { mutableStateOf<String?>(null) }
    var here by remember { mutableStateOf(vm.prefs.lat?.let { la -> vm.prefs.lng?.let { lo -> la to lo } }) }
    var tick by remember { mutableIntStateOf(0) }
    val city = vm.prefs.city.value
    val locate = rememberLocator(vm.prefs) { loc ->
        if (loc != null && (loc.latitude !in 6.0..37.5 || loc.longitude !in 68.0..97.5))
            err = "Your phone reports a location outside India, so there are no showrooms to show. Turn on precise location and try again."
        else if (loc != null) here = loc.latitude to loc.longitude
        else err = "Location is off or not allowed. Turn it on to see showrooms near you."
    }
    LaunchedEffect(Unit) { if (here == null) locate() }
    LaunchedEffect(type) { brands = runCatching { vm.api.brands(city, type) }.getOrElse { emptyList() }.filter { it.models > 0 }.sortedByDescending { it.models } }
    LaunchedEffect(here, type, brand, tick) {
        val h = here ?: return@LaunchedEffect
        list = null; err = null
        runCatching { vm.api.dealersNear(h.first, h.second, brand, type) }
            .onSuccess { list = it }.onFailure { err = "Couldn't reach OnRoad. Check your connection." }
    }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 24.dp)) {
        item {
            ScreenHeader("Showrooms near you", "Official dealers, nearest first", onBack)
            Column(Modifier.padding(horizontal = 16.dp)) {
                Pills(listOf("car" to "Car showrooms", "bike" to "Bike showrooms"), type) { type = it; brand = null }
            }
            LazyRow(contentPadding = PaddingValues(16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                item { BrandPill("All brands", brand == null) { brand = null } }
                items(brands, key = { it.slug }) { b -> BrandPill(b.name, brand == b.slug) { brand = b.slug } }
            }
        }
        val l = list
        when {
            err != null -> item { ErrorState(err!!) { err = null; if (here == null) locate() else tick++ } }
            here == null -> item {
                Column(Modifier.fillMaxWidth().padding(32.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    CircularProgressIndicator(color = Ignition); Text("Finding your location…", color = Mute)
                }
            }
            l == null -> item { Box(Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator(color = Ignition) } }
            l.isEmpty() -> item { Text("No listed showroom within about 300 km. Try another brand.", color = Mute, modifier = Modifier.padding(20.dp)) }
            else -> items(l, key = { it.id }) { d ->
                Tile(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp), pad = 14) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Chip(d.brandName, Ignition); Spacer(Modifier.width(8.dp))
                                d.distanceKm?.let { Text("%.1f km".format(it), color = Electric, fontWeight = FontWeight.SemiBold) }
                            }
                            Spacer(Modifier.height(6.dp))
                            Text(d.name, style = MaterialTheme.typography.titleMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
                            Text(listOfNotNull(d.address.ifBlank { null }, d.city).joinToString(", "), color = Mute,
                                style = MaterialTheme.typography.bodySmall, maxLines = 2)
                        }
                        Column {
                            d.phone?.let { ph ->
                                IconButton({ ctx.startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + ph.split(',', '/', ';')[0].trim()))) }) {
                                    Icon(Icons.Outlined.Call, "Call", tint = Good)
                                }
                            }
                            if (d.lat != null && d.lng != null) IconButton({
                                ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://www.google.com/maps/dir/?api=1&destination=${d.lat},${d.lng}")))
                            }) { Icon(Icons.Outlined.Directions, "Directions", tint = Electric) }
                        }
                    }
                }
            }
        }
        item {
            Row(Modifier.fillMaxWidth().padding(16.dp).clickable { here = null; locate() }, horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.MyLocation, null, tint = Mute, modifier = Modifier.size(16.dp)); Spacer(Modifier.width(6.dp))
                Text("Refresh my location", color = Mute)
            }
        }
    }
}

@Composable
private fun BrandPill(label: String, on: Boolean, onClick: () -> Unit) = Text(label, style = MaterialTheme.typography.labelLarge,
    color = if (on) Color.White else Mute,
    modifier = Modifier.clip(RoundedCornerShape(50)).background(if (on) Ignition else Panel2).clickable(onClick = onClick)
        .padding(horizontal = 14.dp, vertical = 9.dp))
