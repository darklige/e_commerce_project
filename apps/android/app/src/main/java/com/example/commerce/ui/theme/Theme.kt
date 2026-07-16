package com.example.commerce.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val CommerceLightScheme = lightColorScheme(
    primary = Color(0xFFD71920),
    secondary = Color(0xFF007D78),
    tertiary = Color(0xFFB7791F)
)

@Composable
fun CommerceTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = CommerceLightScheme,
        content = content
    )
}

