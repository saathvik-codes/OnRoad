package com.onroad.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import coil3.compose.AsyncImage
import com.onroad.app.data.NewsItem
import com.onroad.app.data.Track
import com.onroad.app.data.UpdateItem
import kotlinx.coroutines.delay

private val TOPIC = mapOf("launch" to "Launch", "price" to "Price", "safety" to "Safety", "ev" to "Electric", "policy" to "Rules & tax",
    "sales" to "Sales", "spied" to "Spotted testing", "industry" to "Industry")

private fun ago(iso: String): String = runCatching {
    val h = ((System.currentTimeMillis() - java.time.Instant.parse(iso).toEpochMilli()) / 3_600_000).coerceAtLeast(1)
    if (h < 24) "${h}h ago" else "${h / 24}d ago"
}.getOrDefault("")

private fun open(ctx: android.content.Context, url: String) = ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))

/** Home: the latest stories as full-width cards that advance on their own. */
@Composable
fun NewsCarousel(news: List<NewsItem>, onModel: (String) -> Unit, onAll: () -> Unit) {
    val slides = news.filter { it.imageUrl != null }.take(6)
    if (slides.isEmpty()) return
    val ctx = LocalContext.current
    val pager = rememberPagerState { slides.size }
    LaunchedEffect(pager.currentPage, slides.size) { delay(6000); if (slides.size > 1) pager.animateScrollToPage((pager.currentPage + 1) % slides.size) }
    Column {
        Row(verticalAlignment = Alignment.Bottom) {
            Text("What's new", style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
            Text("All updates", color = Ignition, style = MaterialTheme.typography.labelLarge, modifier = Modifier.clickable(onClick = onAll))
        }
        Spacer(Modifier.height(10.dp))
        HorizontalPager(pager, pageSpacing = 12.dp) { i ->
            val n = slides[i]
            Box(Modifier.fillMaxWidth().aspectRatio(16 / 10f).clip(RoundedCornerShape(22.dp)).background(Panel2)
                .clickable { Track.news(n.source, n.topic); if (n.modelId != null) onModel(n.modelId) else open(ctx, n.url) }) {
                AsyncImage(n.imageUrl, null, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
                Box(Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Color.Transparent, Color.Black.copy(alpha = 0.8f)))))
                Column(Modifier.align(Alignment.BottomStart).padding(16.dp)) {
                    Text("${TOPIC[n.topic] ?: "News"} · ${n.source} · ${ago(n.published)}".uppercase(), color = Color.White.copy(alpha = 0.8f),
                        style = MaterialTheme.typography.labelSmall)
                    Spacer(Modifier.height(4.dp))
                    Text(n.title, color = Color.White, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, maxLines = 3,
                        overflow = TextOverflow.Ellipsis)
                    if (n.modelId != null) Text("${n.modelName ?: "This car"}: see on-road price", color = Color.White.copy(alpha = 0.85f),
                        style = MaterialTheme.typography.labelMedium, modifier = Modifier.padding(top = 6.dp))
                }
            }
        }
        Row(Modifier.fillMaxWidth().padding(top = 10.dp), horizontalArrangement = Arrangement.spacedBy(5.dp, Alignment.CenterHorizontally)) {
            repeat(slides.size) { k -> Box(Modifier.height(4.dp).width(if (k == pager.currentPage) 20.dp else 8.dp).clip(Corner)
                .background(if (k == pager.currentPage) Ignition else Line)) }
        }
    }
}

/** Updates: news from publishers, and price changes / new models / new offers from makers' own data. */
@Composable
fun UpdatesScreen(onBack: () -> Unit, onModel: (String) -> Unit, vm: BrowseVM = hiltViewModel()) {
    val ctx = LocalContext.current
    var tab by rememberKept("updates.tab") { "news" }
    var topic by rememberKept<String?>("updates.topic") { null }
    var news by remember { mutableStateOf<List<NewsItem>?>(null) }
    var ups by remember { mutableStateOf<List<UpdateItem>?>(null) }
    LaunchedEffect(topic) { news = runCatching { vm.api.news(60, topic) }.getOrElse { emptyList() } }
    LaunchedEffect(Unit) { ups = runCatching { vm.api.updates("car", 80) }.getOrElse { emptyList() } }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 32.dp)) {
        item { ScreenHeader("Updates", "News, launches and price changes", onBack) }
        item {
            Row(Modifier.padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("news" to "News", "prices" to "Prices & launches").forEach { (k, l) ->
                    Text(l, color = if (tab == k) Color.White else Ink, style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.clip(Corner).background(if (tab == k) Ignition else Panel2).clickable { tab = k }.padding(horizontal = 14.dp, vertical = 8.dp))
                }
            }
        }
        if (tab == "news") {
            item {
                Row(Modifier.horizontalScroll(rememberScrollState()).padding(16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    (listOf<String?>(null) + TOPIC.keys.filter { it != "industry" }).forEach { t ->
                        Text(t?.let { TOPIC[it] } ?: "All", color = if (topic == t) Ink else Mute, style = MaterialTheme.typography.labelLarge,
                            fontWeight = if (topic == t) FontWeight.SemiBold else FontWeight.Normal,
                            modifier = Modifier.clickable { topic = t }.padding(vertical = 4.dp))
                    }
                }
            }
            val list = news
            if (list == null) item { Text("Loading…", color = Mute, modifier = Modifier.padding(16.dp)) }
            else if (list.isEmpty()) item { Text("No stories here yet.", color = Mute, modifier = Modifier.padding(16.dp)) }
            else items(list, key = { it.id }) { n ->
                Row(Modifier.fillMaxWidth().clickable { Track.news(n.source, n.topic); open(ctx, n.url) }.padding(horizontal = 16.dp, vertical = 10.dp)) {
                    Column(Modifier.weight(1f)) {
                        Text("${TOPIC[n.topic] ?: "News"} · ${n.source} · ${ago(n.published)}", color = Mute, style = MaterialTheme.typography.labelSmall)
                        Text(n.title, style = MaterialTheme.typography.titleSmall, maxLines = 3, overflow = TextOverflow.Ellipsis)
                        if (n.modelId != null) Text("${n.modelName}: on-road price", color = Ignition, style = MaterialTheme.typography.labelMedium,
                            modifier = Modifier.padding(top = 4.dp).clickable { onModel(n.modelId) })
                    }
                    if (n.imageUrl != null) { Spacer(Modifier.width(12.dp))
                        AsyncImage(n.imageUrl, null, contentScale = ContentScale.Crop, modifier = Modifier.size(96.dp, 72.dp).clip(RoundedCornerShape(12.dp)).background(Panel2)) }
                }
            }
        } else {
            val list = ups
            if (list == null) item { Text("Loading…", color = Mute, modifier = Modifier.padding(16.dp)) }
            else {
                val launches = list.filter { it.kind == "new" }
                val prices = list.filter { it.kind == "price" }
                item { Text("New on the market", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(16.dp)) }
                if (launches.isEmpty()) item { Text("No new models in the last four months.", color = Mute, modifier = Modifier.padding(horizontal = 16.dp)) }
                items(launches, key = { "n" + it.title }) { u -> UpdateRow(u, vm) { u.modelId?.let(onModel) } }
                item { Text("Price changes", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(16.dp)) }
                if (prices.isEmpty()) item { Text("No lasting price changes in the last four months.", color = Mute, modifier = Modifier.padding(horizontal = 16.dp)) }
                items(prices, key = { "p" + it.title + it.date }) { u -> UpdateRow(u, vm) { u.modelId?.let(onModel) } }
            }
        }
    }
}

@Composable
private fun UpdateRow(u: UpdateItem, vm: BrowseVM, onClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 5.dp).clip(RoundedCornerShape(16.dp)).background(Panel)
        .border(1.dp, Line, RoundedCornerShape(16.dp)).clickable(onClick = onClick).padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
        AsyncImage(vm.prefs.img(u.imageUrl, 320), null, contentScale = ContentScale.Fit, modifier = Modifier.size(84.dp, 56.dp))
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text(u.title.removePrefix("New: "), style = MaterialTheme.typography.titleSmall, maxLines = 2)
            Text("${u.date} · ${u.detail}", color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 2)
        }
    }
}
