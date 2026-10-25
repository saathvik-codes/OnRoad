package com.onroad.app.ui

import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil3.compose.SubcomposeAsyncImage
import com.onroad.app.data.GalleryItem

/**
 * Swipeable photo carousel for a model: the selected variant's own photo first, then the model shot and the
 * manufacturer's feature photos. Car shots are shown whole (Fit); feature photos fill the frame (Crop).
 */
@Composable
fun Gallery(items: List<GalleryItem>, variantImage: String?, variantName: String?, img: (String?) -> String?) {
    val shots = buildList {
        variantImage?.let { add(GalleryItem(it, variantName ?: "", "variant")) }
        items.forEach { g -> if (none { it.url == g.url }) add(g) }
    }
    if (shots.isEmpty()) return
    val pager = rememberPagerState { shots.size }
    // switching variant jumps back to that variant's photo
    LaunchedEffect(variantImage) { if (pager.currentPage != 0) pager.scrollToPage(0) }
    Column(Modifier.fillMaxWidth()) {
        Box(Modifier.fillMaxWidth().aspectRatio(16 / 10f)) {
            HorizontalPager(pager, Modifier.fillMaxSize()) { i ->
                val s = shots[i]
                val car = s.kind != "feature"
                Box(Modifier.fillMaxSize().padding(horizontal = 12.dp).clip(RoundedCornerShape(22.dp))
                    .background(if (car) Color.Transparent else Panel), contentAlignment = Alignment.Center) {
                    SubcomposeAsyncImage(img(s.url), s.label, contentScale = if (car) ContentScale.Fit else ContentScale.Crop,
                        modifier = Modifier.fillMaxSize(),
                        loading = { Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator(color = Ignition, strokeWidth = 2.dp) } },
                        error = { Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("Photo unavailable", color = Mute) } })
                    if (!car && s.label.isNotBlank()) Text(s.label, style = MaterialTheme.typography.labelLarge, color = Color.White, maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.align(Alignment.BottomStart).padding(12.dp).clip(Corner)
                            .background(Color.Black.copy(alpha = 0.55f)).padding(horizontal = 12.dp, vertical = 6.dp))
                }
            }
            if (shots.size > 1) Text("${pager.currentPage + 1} / ${shots.size}", style = MaterialTheme.typography.labelMedium, color = Color.White,
                modifier = Modifier.align(Alignment.TopEnd).padding(top = 10.dp, end = 24.dp).clip(Corner)
                    .background(Color.Black.copy(alpha = 0.5f)).padding(horizontal = 10.dp, vertical = 4.dp))
        }
        if (shots.size > 1) Row(Modifier.fillMaxWidth().padding(top = 10.dp), horizontalArrangement = Arrangement.Center) {
            val shown = shots.size.coerceAtMost(9)
            repeat(shown) { i ->
                val on = pager.currentPage.coerceAtMost(shown - 1) == i
                val w by animateDpAsState(if (on) 18.dp else 6.dp, label = "dot")
                Box(Modifier.padding(horizontal = 3.dp).height(6.dp).width(w).clip(CircleShape).background(if (on) Ignition else Line))
            }
        }
    }
}
