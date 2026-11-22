package com.onroad.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.onroad.app.data.Waiting
import com.onroad.app.data.WaitingIn
import kotlinx.coroutines.launch

/** Delivery waiting period from dealer quotes and buyer reports (last 120 days). No reports = no number. */
@Composable
fun WaitingCard(modelId: String, modelName: String, city: String, onSignIn: () -> Unit, vm: BrowseVM) {
    var w by remember(modelId, city) { mutableStateOf<Waiting?>(null) }
    var tick by remember { mutableIntStateOf(0) }
    var telling by remember { mutableStateOf(false) }
    var weeks by remember { mutableFloatStateOf(6f) }
    var note by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    LaunchedEffect(modelId, city, tick) { w = runCatching { vm.api.waiting(modelId, city) }.getOrNull() }
    Column(Modifier.fillMaxWidth().padding(top = 16.dp).clip(Corner).background(Panel2).padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("Waiting period", style = MaterialTheme.typography.titleMedium)
                Text("From dealer quotes and buyers who booked", color = Mute, style = MaterialTheme.typography.bodySmall)
            }
            Art("hero-waiting-period", Modifier.size(width = 84.dp, height = 56.dp))
        }
        val d = w
        if (d?.available == true && d.medianWeeks != null) {
            val med = d.medianWeeks.toInt()
            Text(if (med == 0) "Ready stock" else "About $med ${if (med == 1) "week" else "weeks"}", style = MaterialTheme.typography.headlineSmall)
            Text(listOfNotNull("range ${d.minWeeks}–${d.maxWeeks} weeks".takeIf { d.minWeeks != d.maxWeeks },
                "in ${d.place}", "${d.dealerQuotes + d.buyerReports} reports in the last 4 months").joinToString(" · "),
                color = Mute, style = MaterialTheme.typography.bodySmall)
        } else if (d != null) {
            Text("No reports for the $modelName in $city yet.", color = Mute)
        }
        if (!telling) Text("Booked one? Tell others how long it took", color = Ignition, style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.clickable { telling = true }.padding(vertical = 4.dp))
        else Column {
            Text("${weeks.toInt()} weeks from booking to delivery", fontWeight = FontWeight.SemiBold)
            Slider(weeks, { weeks = it }, valueRange = 0f..40f, steps = 39, colors = SliderDefaults.colors(thumbColor = Ignition, activeTrackColor = Ignition))
            Row(horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                Text("Send", color = Ignition, fontWeight = FontWeight.SemiBold, modifier = Modifier.clickable {
                    scope.launch {
                        runCatching { vm.api.reportWaiting(WaitingIn(modelId, city, weeks.toInt())) }
                            .onSuccess { telling = false; note = "Thanks, that helps the next buyer."; tick++ }
                            .onFailure { note = "Sign in to share, so reports stay honest."; onSignIn() }
                    }
                })
                Text("Cancel", color = Mute, modifier = Modifier.clickable { telling = false })
            }
        }
        note?.let { Text(it, color = Mute, style = MaterialTheme.typography.bodySmall) }
    }
}
