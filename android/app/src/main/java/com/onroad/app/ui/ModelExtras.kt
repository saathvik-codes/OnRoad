package com.onroad.app.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.TrendingDown
import androidx.compose.material.icons.outlined.TrendingFlat
import androidx.compose.material.icons.outlined.TrendingUp
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.onroad.app.data.ModelDetail
import com.onroad.app.data.PricePoint
import com.onroad.app.data.Reco
import kotlin.math.abs
import kotlin.math.roundToLong

/** How this variant's ex-showroom price has moved since OnRoad first read it (every change is kept, nothing is guessed). */
@Composable
fun PriceTrend(history: List<PricePoint>, variantId: String, city: String) {
    val pts = history.filter { it.variantId == variantId && it.city.equals(city, true) }.sortedBy { it.fetchedAt }
        .fold(mutableListOf<PricePoint>()) { acc, p -> if (acc.lastOrNull()?.exShowroomInr != p.exShowroomInr) acc.add(p); acc }
    if (pts.isEmpty()) return
    val first = pts.first(); val last = pts.last()
    val diff = last.exShowroomInr - first.exShowroomInr
    Tile(Modifier.fillMaxWidth().padding(start = 16.dp, end = 16.dp, top = 12.dp)) {
        Column {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(if (diff < 0) Icons.Outlined.TrendingDown else if (diff > 0) Icons.Outlined.TrendingUp else Icons.Outlined.TrendingFlat, null,
                    tint = if (diff < 0) Good else if (diff > 0) Amber else Mute)
                Spacer(Modifier.width(8.dp))
                Text("PRICE TREND · $city", style = MaterialTheme.typography.labelSmall, color = Mute)
            }
            Text(when {
                pts.size == 1 -> "No change since ${first.fetchedAt.take(10)}"
                diff < 0 -> "${rupees(abs(diff))} cheaper than on ${first.fetchedAt.take(10)}"
                diff > 0 -> "${rupees(diff)} dearer than on ${first.fetchedAt.take(10)}"
                else -> "Back to its ${first.fetchedAt.take(10)} price"
            }, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(top = 4.dp))
            if (pts.size >= 2) {
                val lo = pts.minOf { it.exShowroomInr }.toFloat(); val hi = pts.maxOf { it.exShowroomInr }.toFloat()
                Canvas(Modifier.fillMaxWidth().height(56.dp).padding(vertical = 8.dp)) {
                    val step = size.width / (pts.size - 1)
                    fun y(v: Long) = if (hi == lo) size.height / 2 else size.height - (v - lo) / (hi - lo) * size.height
                    for (i in 1 until pts.size) {
                        drawLine(Ignition, Offset(step * (i - 1), y(pts[i - 1].exShowroomInr)), Offset(step * i, y(pts[i].exShowroomInr)), 5f, StrokeCap.Round)
                    }
                    pts.forEachIndexed { i, p -> drawCircle(Ignition, 7f, Offset(step * i, y(p.exShowroomInr))) }
                }
                Text("${pts.size - 1} price change${if (pts.size > 2) "s" else ""} · now ${rupees(last.exShowroomInr)} ex-showroom", color = Mute,
                    style = MaterialTheme.typography.bodySmall)
            } else Text("We check the maker's price every day and will show any change here.", color = Mute, style = MaterialTheme.typography.bodySmall)
        }
    }
}

/** Alternatives a buyer usually cross-shops: same body style, similar on-road price, best matches first. */
@Composable
fun SimilarRow(model: ModelDetail, city: String, vm: BrowseVM, onOpen: (String) -> Unit) {
    var list by remember(model.id, city) { mutableStateOf<List<Reco>>(emptyList()) }
    LaunchedEffect(model.id, city) {
        val prices = model.variants.mapNotNull { it.onroad?.let { b -> b.totalInr - b.refundableInr } ?: it.exShowroomInr }
        if (prices.isEmpty()) return@LaunchedEffect
        val bike = (model.brandVehicleType ?: model.vehicleType) == "bike"
        list = runCatching {
            vm.api.recommendations(city, if (bike) "bike" else "car", (prices.max() * 1.12).roundToLong(), "mixed", 0, null, null, 1000,
                "value,safety", 10, model.bodyType, null, (prices.min() * 0.85).roundToLong())
        }.getOrElse { emptyList() }.filter { it.id != model.id }.take(8)
    }
    if (list.isEmpty()) return
    Column(Modifier.padding(top = 22.dp)) {
        Text("Buyers also consider", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(horizontal = 16.dp))
        Text("Similar price and body style in $city", color = Mute, style = MaterialTheme.typography.bodySmall, modifier = Modifier.padding(horizontal = 16.dp))
        LazyRow(contentPadding = PaddingValues(16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            items(list, key = { it.id }) { r ->
                Tile(Modifier.width(196.dp).clickable { onOpen(r.id) }, pad = 12) {
                    Column {
                        VehicleImage(vm.prefs.img(r.imageUrl, 480), r.name, Modifier.fillMaxWidth().aspectRatio(16 / 10f))
                        Text(r.brand, color = Mute, style = MaterialTheme.typography.labelMedium, maxLines = 1, modifier = Modifier.padding(top = 6.dp))
                        Text(r.name, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        r.fromInr?.let { Text("${rupees(it)} on-road", style = MaterialTheme.typography.bodyMedium) }
                    }
                }
            }
        }
    }
}
