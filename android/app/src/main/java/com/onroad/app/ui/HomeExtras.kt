package com.onroad.app.ui

import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Bolt
import androidx.compose.material.icons.outlined.DirectionsCar
import androidx.compose.material.icons.outlined.TwoWheeler
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil3.compose.SubcomposeAsyncImage
import com.onroad.app.data.OfferItem
import kotlinx.coroutines.delay

/** Manufacturer photo with a quiet loading state and a vehicle silhouette when there's no official photo. */
@Composable
fun VehicleImage(url: String?, desc: String?, modifier: Modifier, bike: Boolean = false, scale: ContentScale = ContentScale.Fit) =
    SubcomposeAsyncImage(url, desc, modifier, contentScale = scale,
        loading = { Box(Modifier.fillMaxSize().clip(RoundedCornerShape(14.dp)).background(Panel2)) },
        error = {
            Box(Modifier.fillMaxSize().clip(RoundedCornerShape(14.dp)).background(Panel2), contentAlignment = Alignment.Center) {
                Icon(if (bike) Icons.Outlined.TwoWheeler else Icons.Outlined.DirectionsCar, null, tint = Mute.copy(alpha = 0.5f), modifier = Modifier.size(40.dp))
            }
        })

/** Auto-advancing banner of live manufacturer offers (same source as the website's offer banner). */
@Composable
fun OffersCarousel(offers: List<OfferItem>, img: (String?) -> String?, onOpen: (OfferItem) -> Unit) {
    if (offers.isEmpty()) return
    val pager = rememberPagerState { offers.size }
    LaunchedEffect(offers.size) {
        while (offers.size > 1) { delay(5000); pager.animateScrollToPage((pager.currentPage + 1) % offers.size) }
    }
    Column {
        HorizontalPager(pager, pageSpacing = 12.dp) { i ->
            val o = offers[i]
            Column(Modifier.fillMaxWidth().height(196.dp).clip(RoundedCornerShape(26.dp))
                .background(Brush.linearGradient(listOf(Panel, Panel)))
                .border(1.dp, Line, RoundedCornerShape(26.dp)).clickable { onOpen(o) }.padding(16.dp)) {
                    Row(Modifier.clip(Corner).background(Ignition.copy(alpha = 0.16f)).padding(horizontal = 9.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Outlined.Bolt, null, tint = Ignition, modifier = Modifier.size(13.dp)); Spacer(Modifier.width(3.dp))
                        Text("MANUFACTURER OFFER", style = MaterialTheme.typography.labelSmall, color = Ignition)
                    }
                    Spacer(Modifier.height(12.dp))
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f).padding(end = 12.dp)) {
                            Text(listOfNotNull(o.brandName, o.modelName).joinToString(" "), style = MaterialTheme.typography.titleMedium, maxLines = 2,
                                overflow = TextOverflow.Ellipsis)
                            o.amountInr?.let { Text("Up to ${rupees(it)}", style = MaterialTheme.typography.titleLarge, color = Good, fontWeight = FontWeight.Bold, maxLines = 1) }
                            Text(o.validUntil?.let { "Valid till $it" } ?: o.title, color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 2,
                                overflow = TextOverflow.Ellipsis)
                        }
                        OfferPhoto(o, img, Modifier.width(140.dp).height(100.dp))
                    }
            }
        }
        if (offers.size > 1) Row(Modifier.fillMaxWidth().padding(top = 10.dp), horizontalArrangement = Arrangement.Center) {
            val n = offers.size.coerceAtMost(8)
            repeat(n) { i ->
                val on = pager.currentPage % n == i
                val w by animateDpAsState(if (on) 18.dp else 6.dp, label = "dot")
                Box(Modifier.padding(horizontal = 3.dp).height(6.dp).width(w).clip(CircleShape).background(if (on) Ignition else Line))
            }
        }
    }
}

/** The offer's car on a light tile (manufacturer shots often have white backgrounds); the brand's logo for brand-wide offers. */
@Composable
fun OfferPhoto(o: OfferItem, img: (String?) -> String?, modifier: Modifier) = Box(
    modifier.clip(RoundedCornerShape(16.dp)).background(Color(0xFFF3F4F7)).padding(6.dp), contentAlignment = Alignment.Center,
) {
    if (o.modelImage != null) VehicleImage(img(o.modelImage), o.modelName, Modifier.fillMaxSize())
    else coil3.compose.AsyncImage(img("/api/logos/${o.brandSlug}"), o.brandName, contentScale = ContentScale.Fit, modifier = Modifier.fillMaxSize(0.7f))
}

data class BudgetChip(val id: String, val label: String, val hint: String)

val BIKE_BUDGET_CHIPS = listOf(BudgetChip("b1", "Under ₹1 lakh", "Commuters, scooters"), BudgetChip("b2", "₹1–2 lakh", "Most popular"),
    BudgetChip("b3", "₹2–5 lakh", "Premium"), BudgetChip("b4", "Above ₹5 lakh", "Superbikes"))

/** "Shop by budget": opens Explore with that budget already selected. */
@Composable
fun BudgetRow(chips: List<BudgetChip>, onPick: (String) -> Unit) =
    LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp), contentPadding = PaddingValues(vertical = 2.dp)) {
        items(chips, key = { it.id }) { c ->
            Column(Modifier.clip(RoundedCornerShape(18.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(18.dp))
                .clickable { onPick(c.id) }.padding(horizontal = 16.dp, vertical = 12.dp)) {
                Text(c.label, fontWeight = FontWeight.SemiBold)
                Text(c.hint, color = Mute, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
