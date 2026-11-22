package com.onroad.app.ui

import android.annotation.SuppressLint
import android.content.Intent
import android.net.Uri
import android.webkit.WebChromeClient
import android.webkit.WebView
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import coil3.compose.AsyncImage
import com.onroad.app.data.ModelVideo

/** Walkarounds, feature explainers and reviews for the model; plays in YouTube's own embedded player. */
@Composable
fun VideosTab(videos: List<ModelVideo>, modelName: String) {
    var playing by remember { mutableStateOf<ModelVideo?>(null) }
    Column(Modifier.padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        if (videos.isEmpty()) Text("No videos of the $modelName yet.", color = Mute, modifier = Modifier.padding(vertical = 20.dp))
        videos.forEach { v ->
            Column(Modifier.fillMaxWidth().clickable { playing = v }) {
                Box(Modifier.fillMaxWidth().aspectRatio(16f / 9f).clip(Corner).background(Color.Black)) {
                    AsyncImage("https://i.ytimg.com/vi/${v.videoId}/hqdefault.jpg", v.title, Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
                    Box(Modifier.align(Alignment.Center).size(52.dp).clip(CircleShape).background(Color.Black.copy(alpha = 0.6f)), contentAlignment = Alignment.Center) {
                        Icon(Icons.Filled.PlayArrow, "Play", tint = Color.White, modifier = Modifier.size(30.dp))
                    }
                }
                Text(v.title, fontWeight = FontWeight.SemiBold, maxLines = 2, overflow = TextOverflow.Ellipsis, modifier = Modifier.padding(top = 8.dp))
                Row {
                    if (v.official == 1) Text("Official  ·  ", color = Ignition, style = MaterialTheme.typography.bodySmall)
                    v.channel?.let { Text(it, color = Mute, style = MaterialTheme.typography.bodySmall) }
                }
            }
        }
    }
    playing?.let { v -> VideoPlayer(v) { playing = null } }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
private fun VideoPlayer(v: ModelVideo, onClose: () -> Unit) {
    val ctx = LocalContext.current
    Dialog(onClose, DialogProperties(usePlatformDefaultWidth = false)) {
        Column(Modifier.fillMaxWidth().background(Color.Black).padding(vertical = 12.dp)) {
            AndroidView({ c ->
                WebView(c).apply {
                    settings.javaScriptEnabled = true
                    settings.mediaPlaybackRequiresUserGesture = false
                    webChromeClient = WebChromeClient()
                    setBackgroundColor(android.graphics.Color.BLACK)
                    // YouTube's player needs a real page origin; the iframe is the documented embed
                    val html = """<html><body style="margin:0;background:#000"><iframe width="100%" height="100%" style="position:absolute;inset:0;border:0"
                        src="https://www.youtube-nocookie.com/embed/${v.videoId}?autoplay=1&playsinline=1&rel=0&origin=https://onroad-uu9c.onrender.com"
                        allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe></body></html>"""
                    loadDataWithBaseURL("https://onroad-uu9c.onrender.com", html, "text/html", "utf-8", null)
                }
            }, Modifier.fillMaxWidth().aspectRatio(16f / 9f), onRelease = { it.destroy() })
            Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 10.dp)) {
                Text(v.title, color = Color.White, maxLines = 2, overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f))
            }
            Row(Modifier.padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                Text("Open in YouTube", color = Ignition, fontWeight = FontWeight.SemiBold, modifier = Modifier.clickable {
                    ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://www.youtube.com/watch?v=${v.videoId}")))
                })
                Text("Close", color = Color.White, fontWeight = FontWeight.SemiBold, modifier = Modifier.clickable(onClick = onClose))
            }
        }
    }
}
