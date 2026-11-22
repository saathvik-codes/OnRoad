package com.onroad.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil3.compose.AsyncImage
import com.onroad.app.data.Reco

/**
 * "For you": cars matched to the budget and body types picked at sign-up, ranked by the server's recommender.
 * Hidden until the buyer has picked something, so it never guesses.
 */
@Composable
fun ForYouRow(onModel: (String) -> Unit, vm: BrowseVM) {
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    val budgetId = vm.prefs.prefBudget
    val bodies = vm.prefs.prefBodies
    var picks by remember { mutableStateOf<List<Reco>>(emptyList()) }
    LaunchedEffect(city, budgetId, bodies) {
        if (budgetId == null && bodies.isEmpty()) return@LaunchedEffect
        val band = runCatching { vm.api.bands() }.getOrDefault(emptyList()).firstOrNull { it.id == budgetId }
        val max = band?.max ?: 3_000_000L
        picks = runCatching {
            vm.api.recommendations(city, "car", max, "mixed", 0, null, null, 1000, "", 10,
                body = bodies.firstOrNull(), budgetMin = band?.min)
        }.getOrDefault(emptyList())
    }
    if (picks.isEmpty()) return
    Column(Modifier.padding(bottom = 22.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("For you", style = MaterialTheme.typography.headlineSmall)
                Text("From your budget and body-type picks", color = Mute, style = MaterialTheme.typography.bodySmall)
            }
            Art("hero-for-you", Modifier.size(width = 84.dp, height = 56.dp))
        }
        LazyRow(contentPadding = PaddingValues(top = 12.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            items(picks, key = { it.id }) { r ->
                Column(Modifier.width(200.dp).clip(RoundedCornerShape(14.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(14.dp))
                    .clickable { onModel(r.id) }.padding(12.dp)) {
                    AsyncImage(vm.prefs.img(r.imageUrl, 480), r.name, Modifier.fillMaxWidth().aspectRatio(16 / 10f), contentScale = ContentScale.Fit)
                    Text("${r.brand} ${r.name}", style = MaterialTheme.typography.titleSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    Text(lakh(r.fromInr), style = MaterialTheme.typography.titleLarge)
                    r.reasons.firstOrNull()?.let { Text(it, color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 2, overflow = TextOverflow.Ellipsis) }
                }
            }
        }
    }
}
