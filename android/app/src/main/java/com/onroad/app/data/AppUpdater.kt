package com.onroad.app.data

import android.app.DownloadManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.Settings
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import com.onroad.app.BuildConfig
import java.io.File

/**
 * Updates the app from inside it. Copies from our website download the new APK in the background (progress in the
 * notification shade) and then open Android's own "Install update?" screen; the first time, Android asks to allow
 * installs from OnRoad. Store builds (build types "amazon" and "play") never install anything themselves: store rules say
 * updates come through the store, so they open OnRoad's store page.
 */
object AppUpdater {
    private const val FILE = "onroad-update.apk"

    private fun storeBuild(ctx: Context): Boolean = BuildConfig.BUILD_TYPE == "amazon" ||
        runCatching {
            if (Build.VERSION.SDK_INT >= 30) ctx.packageManager.getInstallSourceInfo(ctx.packageName).installingPackageName
            else @Suppress("DEPRECATION") ctx.packageManager.getInstallerPackageName(ctx.packageName)
        }.getOrNull() == "com.amazon.venezia"

    fun start(ctx: Context, apkUrl: String) {
        if (BuildConfig.BUILD_TYPE == "play") {
            val p = ctx.packageName
            runCatching { ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=$p")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
                .onFailure { ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://play.google.com/store/apps/details?id=$p")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
            return
        }
        if (storeBuild(ctx)) {
            val p = ctx.packageName
            runCatching { ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("amzn://apps/android?p=$p")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
                .onFailure { ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://www.amazon.com/gp/mas/dl/android?p=$p")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
            return
        }
        if (!ctx.packageManager.canRequestPackageInstalls()) {
            Toast.makeText(ctx, "Allow OnRoad to install updates, then tap Update again", Toast.LENGTH_LONG).show()
            ctx.startActivity(Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:${ctx.packageName}")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            return
        }
        val dir = ctx.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS) ?: return
        val out = File(dir, FILE).apply { delete() }
        val dm = ctx.getSystemService(DownloadManager::class.java)
        val id = dm.enqueue(DownloadManager.Request(Uri.parse(apkUrl))
            .setTitle("OnRoad update")
            .setMimeType("application/vnd.android.package-archive")
            .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE)
            .setDestinationUri(Uri.fromFile(out)))
        Toast.makeText(ctx, "Downloading the update…", Toast.LENGTH_SHORT).show()
        val app = ctx.applicationContext
        ContextCompat.registerReceiver(app, object : BroadcastReceiver() {
            override fun onReceive(c: Context, i: Intent) {
                if (i.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -1) != id) return
                app.unregisterReceiver(this)
                val ok = dm.query(DownloadManager.Query().setFilterById(id)).use { cur ->
                    cur.moveToFirst() && cur.getInt(cur.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS)) == DownloadManager.STATUS_SUCCESSFUL
                }
                if (!ok || !out.exists()) {
                    Toast.makeText(app, "The update didn't download. Check your connection and try again.", Toast.LENGTH_LONG).show()
                    return
                }
                val uri = FileProvider.getUriForFile(app, "${app.packageName}.updates", out)
                app.startActivity(Intent(Intent.ACTION_VIEW).setDataAndType(uri, "application/vnd.android.package-archive")
                    .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK))
            }
        }, IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE), ContextCompat.RECEIVER_EXPORTED)
    }
}
