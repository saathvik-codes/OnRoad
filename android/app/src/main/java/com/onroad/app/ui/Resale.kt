package com.onroad.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.onroad.app.data.Resale

/** Resale value from today's used-car listings for this model in the buyer's city (fetched live by the server). */
@Composable
fun ResaleCard(variantId: String, city: String, modelName: String, vm: BrowseVM = hiltViewModel()) {
    var data by remember(variantId, city) { mutableStateOf<Resale?>(null) }
    var failed by remember(variantId, city) { mutableStateOf(false) }
    var years by remember { mutableIntStateOf(3) }
    val ctx = LocalContext.current
    LaunchedEffect(variantId, city) {
        runCatching { vm.api.resale(variantId, city) }.onSuccess { data = it }.onFailure { failed = true }
    }
    Column(Modifier.fillMaxWidth().padding(top = 16.dp).clip(Corner).background(Panel2).padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("Resale value", style = MaterialTheme.typography.titleMedium)
                Text("What it'll fetch later, from today's used market", color = Mute, style = MaterialTheme.typography.bodySmall)
            }
            Art("hero-resale", Modifier.size(width = 96.dp, height = 64.dp))
        }
        val d = data
        when {
            failed -> Text("Couldn't reach the used-car market right now. Try again in a bit.", color = Mute)
            d == null -> Text("Checking today's used $modelName listings in $city…", color = Mute)
            !d.available -> Text(d.reason ?: "Not enough used $modelName listings yet to estimate resale.", color = Mute)
            else -> {
                Row(Modifier.fillMaxWidth().clip(Corner).background(Night).padding(4.dp)) {
                    d.estimates.map { it.years }.filter { it in listOf(1, 3, 5, 7) }.forEach { y ->
                        Text("$y yr", Modifier.weight(1f).clip(Corner).background(if (y == years) Ignition else Color.Transparent)
                            .clickable { years = y }.padding(vertical = 8.dp), textAlign = TextAlign.Center,
                            color = if (y == years) Color.White else Mute, fontWeight = FontWeight.SemiBold)
                    }
                }
                val est = d.estimates.firstOrNull { it.years == years }
                val pct = if (est != null && (d.exShowroomInr ?: 0) > 0) (est.valueInr * 100 / d.exShowroomInr!!) else null
                Text(lakh(est?.valueInr), style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                Text(listOfNotNull(pct?.let { "keeps about $it% of today's ex-showroom price after $years ${if (years == 1) "year" else "years"}" },
                    d.perYearLossPct?.let { "loses ~$it% a year" }).joinToString(" · "), color = Mute, style = MaterialTheme.typography.bodyMedium)
                if (d.byYear.isNotEmpty()) Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("Asking prices right now", style = MaterialTheme.typography.labelLarge, color = Ink)
                    d.byYear.take(5).forEach { b ->
                        Row(Modifier.fillMaxWidth()) {
                            Text("${b.year} model", Modifier.weight(1f), color = Mute)
                            Text("${lakh(b.medianInr)}  ·  ${b.count} for sale", color = Ink)
                        }
                    }
                }
                Text("From ${d.listings} live used listings in $city, refreshed daily. Actual value depends on condition and km.",
                    color = Mute, style = MaterialTheme.typography.bodySmall)
                d.sourceUrl?.let { u ->
                    Text("See the listings", color = Ignition, style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.clickable { ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(u))) })
                }
            }
        }
    }
}
