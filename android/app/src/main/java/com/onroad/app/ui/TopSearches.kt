package com.onroad.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import com.onroad.app.data.ModelSummary

/**
 * The city's most-bought models as a ranked two-column board: big rank figure, the car, name and starting price.
 * Used by Search and by Compare's picker. `exclude` hides models already chosen.
 */
@Composable
fun TopSearches(city: String, vm: BrowseVM, exclude: Set<String> = emptySet(), title: String = "Top searches in $city",
                onPick: (id: String, label: String) -> Unit) {
    var top by remember(city) { mutableStateOf<List<ModelSummary>>(emptyList()) }
    LaunchedEffect(city) { top = runCatching { vm.api.explore(city, type = "car") }.getOrDefault(emptyList()).take(10) }   // API order = most bought
    val shown = top.filter { it.id !in exclude }.take(8)
    if (shown.isEmpty()) return
    Column(Modifier.padding(horizontal = 16.dp, vertical = 8.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text(title, style = MaterialTheme.typography.titleLarge)
        shown.chunked(2).forEachIndexed { r, pair ->
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                pair.forEachIndexed { c, m ->
                    val rank = r * 2 + c + 1
                    val label = "${m.brand} ${m.name}"
                    Column(Modifier.weight(1f).clip(RoundedCornerShape(14.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(14.dp))
                        .clickable { onPick(m.id, label) }.padding(12.dp)) {
                        Row(verticalAlignment = Alignment.Top) {
                            Text("%02d".format(rank), style = MaterialTheme.typography.headlineSmall, color = if (rank <= 3) Ignition else Mute)
                            Spacer(Modifier.weight(1f))
                            Text(lakh(m.fromInr), style = MaterialTheme.typography.labelLarge, color = Ink)
                        }
                        AsyncImage(vm.prefs.img(m.imageUrl, 480), label, Modifier.fillMaxWidth().aspectRatio(16 / 9f).padding(vertical = 6.dp),
                            contentScale = ContentScale.Fit)
                        Text(m.name, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text(m.brand, color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 1)
                    }
                }
                if (pair.size == 1) Spacer(Modifier.weight(1f))
            }
        }
    }
}
