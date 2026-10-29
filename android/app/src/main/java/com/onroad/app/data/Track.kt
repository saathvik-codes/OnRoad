package com.onroad.app.data

import android.content.Context
import android.os.Bundle
import com.google.firebase.analytics.FirebaseAnalytics

/**
 * Firebase Analytics events for the buyer journey, using Google's recommended event names so the Firebase and
 * Google Ads reports understand them: screen_view, view_item (a car), select_item (a variant), search, view_item_list
 * (a filtered list), add_to_wishlist (saved car), generate_lead (quote request), sign_up / login, select_content
 * (news). No personal data is sent: ids are model / variant ids, never names, emails or phone numbers.
 */
object Track {
    private var fa: FirebaseAnalytics? = null

    fun init(ctx: Context) { if (fa == null) fa = FirebaseAnalytics.getInstance(ctx.applicationContext) }

    private fun log(name: String, vararg p: Pair<String, Any?>) {
        val b = Bundle()
        p.forEach { (k, v) ->
            when (v) {
                null -> {}
                is Long -> b.putLong(k, v)
                is Int -> b.putLong(k, v.toLong())
                is Double -> b.putDouble(k, v)
                else -> b.putString(k, v.toString().take(100))
            }
        }
        runCatching { fa?.logEvent(name, b) }
    }

    fun screen(route: String) = log(FirebaseAnalytics.Event.SCREEN_VIEW, FirebaseAnalytics.Param.SCREEN_NAME to route.substringBefore('/'),
        FirebaseAnalytics.Param.SCREEN_CLASS to route.substringBefore('/'))
    fun viewCar(modelId: String, brand: String, city: String, fromInr: Long?) = log(FirebaseAnalytics.Event.VIEW_ITEM,
        FirebaseAnalytics.Param.ITEM_ID to modelId, FirebaseAnalytics.Param.ITEM_BRAND to brand, "city" to city,
        FirebaseAnalytics.Param.CURRENCY to "INR", FirebaseAnalytics.Param.VALUE to fromInr?.toDouble())
    fun pickVariant(variantId: String, onRoadInr: Long?) = log(FirebaseAnalytics.Event.SELECT_ITEM,
        FirebaseAnalytics.Param.ITEM_ID to variantId, FirebaseAnalytics.Param.CURRENCY to "INR", FirebaseAnalytics.Param.VALUE to onRoadInr?.toDouble())
    fun search(q: String) = log(FirebaseAnalytics.Event.SEARCH, FirebaseAnalytics.Param.SEARCH_TERM to q)
    fun filters(list: String, count: Int, sort: String) = log(FirebaseAnalytics.Event.VIEW_ITEM_LIST,
        FirebaseAnalytics.Param.ITEM_LIST_NAME to list, "filters" to count, "sort" to sort)
    fun saveCar(variantId: String) = log(FirebaseAnalytics.Event.ADD_TO_WISHLIST, FirebaseAnalytics.Param.ITEM_ID to variantId)
    fun quote(variantId: String, city: String, onRoadInr: Long?) = log(FirebaseAnalytics.Event.GENERATE_LEAD,
        FirebaseAnalytics.Param.ITEM_ID to variantId, "city" to city, FirebaseAnalytics.Param.CURRENCY to "INR",
        FirebaseAnalytics.Param.VALUE to onRoadInr?.toDouble())
    fun signUp(method: String) = log(FirebaseAnalytics.Event.SIGN_UP, FirebaseAnalytics.Param.METHOD to method)
    fun login(method: String) = log(FirebaseAnalytics.Event.LOGIN, FirebaseAnalytics.Param.METHOD to method)
    fun news(source: String, topic: String) = log(FirebaseAnalytics.Event.SELECT_CONTENT,
        FirebaseAnalytics.Param.CONTENT_TYPE to "news", "source" to source, "topic" to topic)
}
