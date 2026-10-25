package com.onroad.app.ui

import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage

/** Names of the illustrations bundled in assets/illustrations (published by scripts/illustrations.py). */
private var bundled: Set<String>? = null

fun hasArt(ctx: android.content.Context, name: String): Boolean {
    val names = bundled ?: runCatching { ctx.assets.list("illustrations")?.map { it.substringBeforeLast('.') }?.toSet() }
        .getOrNull().orEmpty().also { bundled = it }
    return name in names
}

/** An illustration if it has been added (design/illustrations -> scripts/illustrations.py); nothing otherwise, so
 *  every screen keeps its current look until its image exists. */
@Composable
fun Art(name: String, modifier: Modifier = Modifier.size(170.dp)) {
    val ctx = LocalContext.current
    if (remember(name) { hasArt(ctx, name) }) {
        AsyncImage("file:///android_asset/illustrations/$name.webp", null, contentScale = ContentScale.Fit, modifier = modifier)
    }
}
