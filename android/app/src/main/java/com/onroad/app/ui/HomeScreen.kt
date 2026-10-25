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
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import javax.inject.Inject

data class HomeState(val type: String = "car", val brands: List<Brand> = emptyList(), val popular: List<ModelSummary> = emptyList(),
                     val offers: List<com.onroad.app.data.OfferItem> = emptyList(), val bands: List<com.onroad.app.data.Band> = emptyList(),
                     val loading: Boolean = true, val error: String? = null)

@HiltViewModel
class HomeVM @Inject constructor(private val api: Api, val prefs: Prefs) : ViewModel() {
    private val _s = MutableStateFlow(HomeState()); val s = _s.asStateFlow()
    private val type = MutableStateFlow("car")
    init { viewModelScope.launch { kotlinx.coroutines.flow.combine(prefs.city, type) { c, t -> c to t }.collectLatest { (c, t) -> load(c, t) } } }
    fun setType(t: String) { type.value = t }
    fun retry() { viewModelScope.launch { load(prefs.city.value, type.value) } }
    private suspend fun load(city: String, t: String) {
        _s.value = _s.value.copy(type = t, loading = true, error = null)
        runCatching { api.brands(city, t) to api.explore(city, type = t).take(10) }
            .onSuccess { (b, p) ->
                val bset = b.map { it.slug }.toSet()
                val offers = runCatching { api.offers(city, 40) }.getOrElse { emptyList() }.filter { it.brandSlug in bset }
                val bands = runCatching { api.bands() }.getOrElse { emptyList() }
                _s.value = HomeState(t, b.filter { it.models > 0 }.sortedByDescending { it.models }, p, offers, bands, false)
            }
            .onFailure { _s.value = _s.value.copy(loading = false, error = "Can't reach OnRoad. Check your internet connection.") }
    }
}

@Composable
fun HomeScreen(onBrand: (Brand) -> Unit, onModel: (String) -> Unit, onSearch: () -> Unit, onCity: () -> Unit, onCalc: () -> Unit, onAccount: () -> Unit, onOffers: () -> Unit, onFinder: () -> Unit, onShowrooms: () -> Unit,
               onCompare: () -> Unit, onGuide: () -> Unit, onBudget: (type: String, budget: String) -> Unit, vm: HomeVM = hiltViewModel()) {
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
                Text("Most bought in India", style = MaterialTheme.typography.titleLarge)
                Text("Ranked by official monthly sales", color = Mute, style = MaterialTheme.typography.bodySmall)
            }
        }
        items(s.popular.take(6), span = { GridItemSpan(3) }) { m -> PopularRow(m, vm.prefs.img(m.imageUrl, 480)) { onModel(m.id) } }
        item(span = { GridItemSpan(3) }) { Text("Browse by brand", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(top = 14.dp)) }
        items(s.brands, key = { it.slug }) { b -> BrandTile(b, vm.prefs.img(b.logo, 240)) { onBrand(b) } }
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
