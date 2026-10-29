package com.onroad.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.TravelExplore
import androidx.compose.material.icons.automirrored.outlined.CompareArrows
import androidx.compose.material.icons.automirrored.outlined.MenuBook
import androidx.compose.material.icons.outlined.Calculate
import androidx.compose.material.icons.outlined.LocalOffer
import androidx.compose.material.icons.outlined.Storefront
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import coil3.compose.AsyncImage
import com.onroad.app.data.Api
import com.onroad.app.data.Brand
import com.onroad.app.data.ModelSummary
import com.onroad.app.data.Prefs
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import javax.inject.Inject

data class HomeState(val type: String = "car", val brands: List<Brand> = emptyList(), val popular: List<ModelSummary> = emptyList(),
                     val offers: List<com.onroad.app.data.OfferItem> = emptyList(), val bands: List<com.onroad.app.data.Band> = emptyList(),
                     val loading: Boolean = true, val error: String? = null,
                     val rivals: List<Pair<ModelSummary, ModelSummary>> = emptyList())

/** Head-to-head picks from real sales ranks: each best seller against the closest-priced best seller of another
 *  brand with the same body type (e.g. Creta vs Seltos). No made-up popularity, only official monthly sales. */
fun rivalPairs(all: List<ModelSummary>, max: Int = 6): List<Pair<ModelSummary, ModelSummary>> {
    val ranked = all.filter { it.salesRank != null && it.fromInr != null && it.bodyType != null }.sortedBy { it.salesRank }.take(40)
    val used = mutableSetOf<String>(); val out = mutableListOf<Pair<ModelSummary, ModelSummary>>()
    for (a in ranked) {
        if (a.id in used || out.size >= max) continue
        val pa = a.fromInr!!.toDouble()
        val b = ranked.filter { it.id != a.id && it.id !in used && it.bodyType == a.bodyType && it.brandSlug != a.brandSlug &&
            it.fromInr!! / pa in 0.75..1.33 }.minByOrNull { it.salesRank!! } ?: continue
        out += a to b; used += a.id; used += b.id
    }
    return out
}

@HiltViewModel
class HomeVM @Inject constructor(private val api: Api, val prefs: Prefs) : ViewModel() {
    suspend fun news(): List<com.onroad.app.data.NewsItem> = runCatching { api.news(12) }.getOrElse { emptyList() }
    private val _s = MutableStateFlow(HomeState()); val s = _s.asStateFlow()
    private val type = MutableStateFlow("car")
    init { viewModelScope.launch { kotlinx.coroutines.flow.combine(prefs.city, type) { c, t -> c to t }.collectLatest { (c, t) -> load(c, t) } } }
    fun setType(t: String) { type.value = t }
    fun retry() { viewModelScope.launch { load(prefs.city.value, type.value) } }
    private suspend fun load(city: String, t: String) {
        _s.value = _s.value.copy(type = t, loading = true, error = null)
        try {
            coroutineScope {
                val brandsDeferred = async { api.brands(city, t) }
                val exploreDeferred = async { api.explore(city, type = t) }
                val offersDeferred = async { runCatching { api.offers(city, 40) }.getOrElse { emptyList() } }
                val bandsDeferred = async { runCatching { api.bands() }.getOrElse { emptyList() } }

                val b = brandsDeferred.await()
                val all = exploreDeferred.await()
                val p = all.take(10)
                val bset = b.map { it.slug }.toSet()
                val offers = offersDeferred.await().filter { it.brandSlug in bset }
                val bands = bandsDeferred.await()
                _s.value = HomeState(t, b.filter { it.models > 0 }, p, offers, bands, false, rivals = rivalPairs(all))
            }
        } catch (e: Exception) {
            if (_s.value.popular.isEmpty() && _s.value.brands.isEmpty()) {
                _s.value = _s.value.copy(loading = false, error = "Can't reach OnRoad. Check your internet connection.")
            } else {
                _s.value = _s.value.copy(loading = false)
            }
        }
    }
}

@Composable
fun HomeScreen(onBrand: (Brand) -> Unit, onModel: (String) -> Unit, onSearch: () -> Unit, onCity: () -> Unit, onCalc: () -> Unit, onAccount: () -> Unit, onOffers: () -> Unit, onFinder: () -> Unit, onShowrooms: () -> Unit,
               onCompare: () -> Unit, onCompareThese: (String, String) -> Unit = { _, _ -> }, onGuide: () -> Unit, onBudget: (type: String, budget: String) -> Unit, onUpdates: () -> Unit = {}, vm: HomeVM = hiltViewModel()) {
    val newsState = androidx.compose.runtime.remember { androidx.compose.runtime.mutableStateOf<List<com.onroad.app.data.NewsItem>>(emptyList()) }
    val news = newsState.value
    androidx.compose.runtime.LaunchedEffect(Unit) { newsState.value = vm.news() }
    val s by vm.s.collectAsStateWithLifecycle()
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    LazyVerticalGrid(GridCells.Fixed(3), Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp),
        horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item(span = { GridItemSpan(3) }) {
            Column(Modifier.statusBarsPadding()) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("on", style = MaterialTheme.typography.headlineMedium)
                    Text("road", style = MaterialTheme.typography.headlineMedium, color = Ignition)
                    Spacer(Modifier.weight(1f))
                    Row(Modifier.clip(Corner).background(Panel2).clickable(onClick = onCity).padding(horizontal = 12.dp, vertical = 7.dp),
                        verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Outlined.LocationOn, null, tint = Ignition, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(4.dp)); Text(city, style = MaterialTheme.typography.labelLarge)
                    }
                    Spacer(Modifier.width(8.dp))
                    Box(Modifier.size(36.dp).clip(Corner).background(Panel2).clickable(onClick = onAccount), contentAlignment = Alignment.Center) {
                        Icon(androidx.compose.material.icons.Icons.Outlined.Person, "My garage", tint = Ink, modifier = Modifier.size(20.dp))
                    }
                }
                Spacer(Modifier.height(16.dp))
                Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(18.dp)).background(Panel2).clickable(onClick = onSearch).padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Outlined.Search, null, tint = Mute); Spacer(Modifier.width(10.dp))
                    Text(if (s.type == "bike") "Search Splendor, Activa, Classic 350…" else "Search Creta, Nexon, Thar…", color = Mute)
                }
                Spacer(Modifier.height(12.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    listOf("car" to "Cars", "bike" to "Bikes").forEach { (k, l) ->
                        Text(l, style = MaterialTheme.typography.labelLarge, color = if (s.type == k) Color.White else Mute,
                            modifier = Modifier.clip(Corner).background(if (s.type == k) Ignition else Panel2)
                                .clickable { vm.setType(k) }.padding(horizontal = 16.dp, vertical = 8.dp))
                    }
                }
                Spacer(Modifier.height(16.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    QuickAction(Icons.Outlined.TravelExplore, if (s.type == "bike") "Find my\nbike" else "Find my\ncar", Ignition, Modifier.weight(1f), onFinder)
                    QuickAction(Icons.Outlined.Storefront, "Showrooms\nnear me", Amber, Modifier.weight(1f), onShowrooms)
                    QuickAction(Icons.AutoMirrored.Outlined.CompareArrows, "Compare", Electric, Modifier.weight(1f), onCompare)
                    QuickAction(Icons.AutoMirrored.Outlined.MenuBook, "Buying\nguide", Good, Modifier.weight(1f), onGuide)
                }
                s.error?.let { ErrorState(it) { vm.retry() } }
                Spacer(Modifier.height(22.dp))
                if (news.isNotEmpty()) { NewsCarousel(news, onModel, onUpdates); Spacer(Modifier.height(22.dp)) }
                if (s.offers.isNotEmpty()) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Live offers in $city", style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
                        Text("See all", color = Ignition, modifier = Modifier.clickable(onClick = onOffers).padding(6.dp))
                    }
                    Spacer(Modifier.height(10.dp))
                    OffersCarousel(s.offers.take(8), { vm.prefs.img(it, 480) }) { onOffers() }
                    Spacer(Modifier.height(22.dp))
                }
                val chips = if (s.type == "bike") BIKE_BUDGET_CHIPS else s.bands.map { BudgetChip(it.id, it.label, it.hint) }
                if (chips.isNotEmpty()) {
                    Text("Shop by budget", style = MaterialTheme.typography.titleLarge)
                    Text("On-road prices for $city inside", color = Mute, style = MaterialTheme.typography.bodySmall)
                    Spacer(Modifier.height(10.dp))
                    BudgetRow(chips) { onBudget(s.type, it) }
                    Spacer(Modifier.height(22.dp))
                }
                if (s.rivals.isNotEmpty()) {
                    Text("Top picks to compare", style = MaterialTheme.typography.titleLarge)
                    Text("Best-selling rivals, same body type and budget", color = Mute, style = MaterialTheme.typography.bodySmall)
                    Spacer(Modifier.height(10.dp))
                    androidx.compose.foundation.lazy.LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        items(s.rivals.size) { i -> val (a, b) = s.rivals[i]
                            RivalCard(a, b, { vm.prefs.img(it, 480) }) { onCompareThese(a.id, b.id) } }
                    }
                    Spacer(Modifier.height(22.dp))
                }
                Text("Top buys in India", style = MaterialTheme.typography.titleLarge)
                Text("Ranked by official monthly sales", color = Mute, style = MaterialTheme.typography.bodySmall)
            }
        }
        if (s.loading && s.popular.isEmpty()) {
            item(span = { GridItemSpan(3) }) {
                Row(
                    Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Panel2.copy(alpha = 0.7f)).padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    androidx.compose.material3.CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        strokeWidth = 2.5.dp,
                        color = Ignition
                    )
                    Column {
                        Text("Loading latest on-road prices…", style = MaterialTheme.typography.titleSmall, color = Ink)
                        Text("Connecting to server & official price catalogue", style = MaterialTheme.typography.bodySmall, color = Mute)
                    }
                }
            }
            items(3, span = { GridItemSpan(3) }) {
                SkeletonPopularRow()
            }
        } else {
            items(s.popular.take(6), span = { GridItemSpan(3) }) { m -> PopularRow(m, vm.prefs.img(m.imageUrl, 480)) { onModel(m.id) } }
        }
        item(span = { GridItemSpan(3) }) { Text("Browse by brand", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(top = 14.dp)) }
        if (s.loading && s.brands.isEmpty()) {
            items(6) {
                SkeletonBrandTile()
            }
        } else {
            items(s.brands, key = { it.slug }) { b -> BrandTile(b, vm.prefs.img(b.logo, 240)) { onBrand(b) } }
        }
    }
}

@Composable
private fun PopularRow(m: ModelSummary, img: String?, onClick: () -> Unit) = Tile(Modifier.fillMaxWidth().clickable(onClick = onClick), pad = 12) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        VehicleImage(img, m.name, Modifier.width(130.dp).aspectRatio(16 / 10f))
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            m.salesRank?.let { Chip("#$it in India", Ignition) }
            Spacer(Modifier.height(4.dp))
            Text("${m.brand} ${m.name}", style = MaterialTheme.typography.titleMedium, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text(range(m.fromInr, m.toInr), color = Mute)
        }
    }
}

@Composable
private fun RivalCard(a: ModelSummary, b: ModelSummary, img: (String?) -> String?, onClick: () -> Unit) =
    Tile(Modifier.width(310.dp).clickable(onClick = onClick), pad = 12) {
        Column {
            Row(verticalAlignment = Alignment.CenterVertically) {
                listOf(a, b).forEachIndexed { i, m ->
                    if (i == 1) Text("VS", style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.Black, color = Ignition,
                        modifier = Modifier.padding(horizontal = 6.dp))
                    Column(Modifier.weight(1f)) {
                        VehicleImage(img(m.imageUrl), m.name, Modifier.fillMaxWidth().aspectRatio(16 / 10f))
                        Spacer(Modifier.height(6.dp))
                        Text(m.brand, color = Mute, style = MaterialTheme.typography.labelSmall, maxLines = 1)
                        Text(m.name, style = MaterialTheme.typography.titleSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text(lakh(m.fromInr ?: 0) + " onwards", color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 1)
                        m.salesRank?.let { Chip("#$it in sales", Good, Modifier.padding(top = 4.dp)) }
                    }
                }
            }
            Spacer(Modifier.height(10.dp))
            Text("Compare on-road prices  →", color = Ignition, fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.labelLarge)
        }
    }

@Composable
private fun BrandTile(b: Brand, logo: String?, onClick: () -> Unit) = Box(
    Modifier.aspectRatio(1f).clip(RoundedCornerShape(18.dp)).background(Color.White).clickable(onClick = onClick).padding(10.dp),
    contentAlignment = Alignment.Center,
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        if (logo != null) AsyncImage(logo, b.name, contentScale = ContentScale.Fit, modifier = Modifier.height(38.dp).fillMaxWidth())
        else Text(b.name, color = Color.Black, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(6.dp))
        Text(b.fromInr?.let { "from ${lakh(it)}" } ?: "${b.models} models", color = Color(0xFF555B6E), style = MaterialTheme.typography.labelSmall)
    }
}

@Composable
private fun QuickAction(icon: ImageVector, label: String, tint: Color, modifier: Modifier, onClick: () -> Unit) = Column(
    modifier.clip(RoundedCornerShape(18.dp)).background(Panel).clickable(onClick = onClick).padding(vertical = 14.dp, horizontal = 6.dp),
    horizontalAlignment = Alignment.CenterHorizontally,
) {
    Box(Modifier.size(40.dp).clip(RoundedCornerShape(12.dp)).background(tint.copy(alpha = 0.14f)), contentAlignment = Alignment.Center) {
        Icon(icon, null, tint = tint, modifier = Modifier.size(22.dp))
    }
    Spacer(Modifier.height(8.dp))
    Text(label, style = MaterialTheme.typography.labelMedium, textAlign = androidx.compose.ui.text.style.TextAlign.Center, maxLines = 2)
}

@Composable
private fun SkeletonPopularRow() = Tile(Modifier.fillMaxWidth(), pad = 12) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.width(130.dp).aspectRatio(16 / 10f).clip(RoundedCornerShape(14.dp)).background(Panel2))
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Box(Modifier.width(70.dp).height(18.dp).clip(Corner).background(Panel2))
            Spacer(Modifier.height(8.dp))
            Box(Modifier.fillMaxWidth(0.85f).height(18.dp).clip(Corner).background(Panel2))
            Spacer(Modifier.height(6.dp))
            Box(Modifier.fillMaxWidth(0.5f).height(14.dp).clip(Corner).background(Panel2))
        }
    }
}

@Composable
private fun SkeletonBrandTile() = Box(
    Modifier.aspectRatio(1f).clip(RoundedCornerShape(18.dp)).background(Color.White.copy(alpha = 0.85f)).padding(10.dp),
    contentAlignment = Alignment.Center,
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Box(Modifier.size(36.dp).clip(RoundedCornerShape(8.dp)).background(Panel2))
        Spacer(Modifier.height(8.dp))
        Box(Modifier.width(52.dp).height(12.dp).clip(Corner).background(Panel2))
    }
}

