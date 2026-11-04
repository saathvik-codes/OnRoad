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

/** Updates: news from publishers, and launches / price changes / offers from makers' own data. */
@OptIn(androidx.compose.foundation.ExperimentalFoundationApi::class)
@Composable
fun UpdatesScreen(onBack: () -> Unit, onModel: (String) -> Unit, vm: BrowseVM = hiltViewModel()) {
    val ctx = LocalContext.current
    var tab by rememberKept("updates.tab") { "news" }
    var topic by rememberKept<String?>("updates.topic") { null }
    var kind by rememberKept<String?>("updates.kind") { null }
    var news by remember { mutableStateOf<List<NewsItem>?>(null) }
    var ups by remember { mutableStateOf<List<UpdateItem>?>(null) }
    LaunchedEffect(topic) { news = null; news = runCatching { vm.api.news(60, topic) }.getOrElse { emptyList() } }
    LaunchedEffect(Unit) { ups = runCatching { vm.api.updates("car", 80) }.getOrElse { emptyList() } }

    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 32.dp)) {
        item { ScreenHeader("Updates", "News, launches and price changes", onBack) }
        item {
            Segmented(listOf("news" to "News", "prices" to "Prices & launches"), tab, { tab = it },
                Modifier.padding(horizontal = 16.dp).padding(bottom = 4.dp))
        }
        // filters stay pinned under the header while the list scrolls
        stickyHeader(key = "filters-$tab") {
            Box(Modifier.fillMaxWidth().background(MaterialTheme.colorScheme.background)) {
                if (tab == "news") {
                    ChipRow((listOf<String?>(null) + TOPIC.keys.filter { it != "industry" }).map { t -> t to (t?.let { TOPIC[it] } ?: "All") }, topic) { topic = it }
                } else {
                    val l = ups.orEmpty()
                    val counts = mapOf<String?, Int>(null to l.size, "new" to l.count { it.kind == "new" },
                        "price" to l.count { it.kind == "price" }, "offer" to l.count { it.kind == "offer" })
                    ChipRow(listOf(null to "All", "new" to "Launches", "price" to "Price changes", "offer" to "Offers"), kind,
                        counts = if (ups == null) null else counts) { kind = it }
                }
            }
        }
        if (tab == "news") {
            val list = news
            when {
                list == null -> items(5) { SkeletonRow() }
                list.isEmpty() -> item { EmptyNote("No stories in this topic yet.", "Try All, or check back later today.") }
                else -> items(list, key = { it.id }) { n ->
                    Row(Modifier.fillMaxWidth().clickable { Track.news(n.source, n.topic); open(ctx, n.url) }.padding(horizontal = 16.dp, vertical = 12.dp)) {
                        Column(Modifier.weight(1f)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                KindTag(TOPIC[n.topic] ?: "News", Ignition)
                                Spacer(Modifier.width(8.dp))
                                Text("${n.source} · ${ago(n.published)}", color = Mute, style = MaterialTheme.typography.labelSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            }
                            Spacer(Modifier.height(6.dp))
                            Text(n.title, style = MaterialTheme.typography.titleSmall, maxLines = 3, overflow = TextOverflow.Ellipsis)
                            if (n.modelId != null) Text("${n.modelName}: on-road price", color = Ignition, style = MaterialTheme.typography.labelMedium,
                                modifier = Modifier.padding(top = 6.dp).clickable { onModel(n.modelId) })
                        }
                        if (n.imageUrl != null) { Spacer(Modifier.width(12.dp))
                            AsyncImage(n.imageUrl, null, contentScale = ContentScale.Crop, modifier = Modifier.size(96.dp, 72.dp).clip(RoundedCornerShape(12.dp)).background(Panel2)) }
                    }
                }
            }
        } else {
            val list = ups?.filter { kind == null || it.kind == kind }
            when {
                list == null -> items(5) { SkeletonRow() }
                list.isEmpty() -> item {
                    EmptyNote(when (kind) { "new" -> "No new models in the last four months."; "price" -> "No lasting price changes in the last four months."
                        "offer" -> "No current manufacturer offers."; else -> "Nothing new in the last four months." }, "Makers' own websites are checked every few hours.")
                }
                else -> items(list, key = { it.kind + it.title + it.date }) { u -> UpdateRow(u, vm) { u.modelId?.let(onModel) } }
            }
        }
    }
}

/** Two equal options in one rounded track; the chosen one is raised. */
@Composable
private fun Segmented(options: List<Pair<String, String>>, selected: String, onPick: (String) -> Unit, modifier: Modifier = Modifier) {
    Row(modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).background(Panel2).border(1.dp, Line, RoundedCornerShape(14.dp)).padding(4.dp)) {
        options.forEach { (k, label) ->
            val on = k == selected
            Box(Modifier.weight(1f).clip(RoundedCornerShape(10.dp)).background(if (on) Panel else Color.Transparent)
                .then(if (on) Modifier.border(1.dp, Line, RoundedCornerShape(10.dp)) else Modifier)
                .clickable { onPick(k) }.padding(vertical = 10.dp), contentAlignment = Alignment.Center) {
                Text(label, color = if (on) Ink else Mute, style = MaterialTheme.typography.labelLarge, fontWeight = if (on) FontWeight.SemiBold else FontWeight.Medium)
            }
        }
    }
}

/** Scrollable filter chips; the chosen one is tinted with the brand colour. Optional counts; empty filters are hidden. */
@Composable
private fun ChipRow(options: List<Pair<String?, String>>, selected: String?, counts: Map<String?, Int>? = null, onPick: (String?) -> Unit) {
    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal = 16.dp, vertical = 10.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        options.forEach { (k, label) ->
            val on = k == selected
            val n = counts?.get(k)
            if (counts != null && k != null && n == 0 && !on) return@forEach
            Row(Modifier.height(36.dp).clip(RoundedCornerShape(18.dp))
                .background(if (on) Ignition.copy(alpha = 0.12f) else Panel)
                .border(1.dp, if (on) Ignition else Line, RoundedCornerShape(18.dp))
                .clickable { onPick(k) }.padding(horizontal = 14.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(label, color = if (on) Ignition else Ink, style = MaterialTheme.typography.labelLarge,
                    fontWeight = if (on) FontWeight.SemiBold else FontWeight.Medium)
                if (n != null) { Spacer(Modifier.width(6.dp))
                    Text("$n", color = if (on) Ignition else Mute, style = MaterialTheme.typography.labelMedium) }
            }
        }
    }
}

@Composable
private fun KindTag(text: String, color: Color) = Text(text, color = color, style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.SemiBold,
    modifier = Modifier.clip(RoundedCornerShape(6.dp)).background(color.copy(alpha = 0.12f)).padding(horizontal = 7.dp, vertical = 2.dp))

@Composable
private fun SkeletonRow() = Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp)) {
    Column(Modifier.weight(1f)) {
        Box(Modifier.width(110.dp).height(12.dp).clip(RoundedCornerShape(6.dp)).background(Panel2))
        Spacer(Modifier.height(10.dp))
        Box(Modifier.fillMaxWidth().height(14.dp).clip(RoundedCornerShape(6.dp)).background(Panel2))
        Spacer(Modifier.height(6.dp))
        Box(Modifier.fillMaxWidth(0.7f).height(14.dp).clip(RoundedCornerShape(6.dp)).background(Panel2))
    }
    Spacer(Modifier.width(12.dp))
    Box(Modifier.size(96.dp, 72.dp).clip(RoundedCornerShape(12.dp)).background(Panel2))
}

@Composable
private fun EmptyNote(title: String, sub: String) = Column(Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 36.dp),
    horizontalAlignment = Alignment.CenterHorizontally) {
    Text(title, style = MaterialTheme.typography.titleSmall, color = Ink)
    Spacer(Modifier.height(4.dp))
    Text(sub, style = MaterialTheme.typography.bodySmall, color = Mute)
}

@Composable
private fun UpdateRow(u: UpdateItem, vm: BrowseVM, onClick: () -> Unit) {
    val down = u.kind == "price" && Regex("cut|lower|drop|reduc", RegexOption.IGNORE_CASE).containsMatchIn(u.title + " " + u.detail)
    val (tag, color) = when (u.kind) {
        "new" -> "New launch" to Ignition
        "offer" -> "Offer" to Good
        "price" -> if (down) "Price cut" to Good else "Price rise" to Amber
        else -> "Update" to Mute
    }
    Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 5.dp).clip(RoundedCornerShape(16.dp)).background(Panel)
        .border(1.dp, Line, RoundedCornerShape(16.dp)).clickable(onClick = onClick).padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(88.dp, 60.dp).clip(RoundedCornerShape(10.dp)).background(Panel2), contentAlignment = Alignment.Center) {
            AsyncImage(vm.prefs.img(u.imageUrl, 320), null, contentScale = ContentScale.Fit, modifier = Modifier.fillMaxSize().padding(4.dp))
        }
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                KindTag(tag, color); Spacer(Modifier.width(8.dp))
                Text(u.date, color = Mute, style = MaterialTheme.typography.labelSmall)
            }
            Spacer(Modifier.height(4.dp))
            Text(u.title.removePrefix("New: "), style = MaterialTheme.typography.titleSmall, maxLines = 2, overflow = TextOverflow.Ellipsis)
            Text(u.detail, color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 2, overflow = TextOverflow.Ellipsis)
        }
    }
}
