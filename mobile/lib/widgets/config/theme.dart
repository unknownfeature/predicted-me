import 'package:flutter/material.dart';
import 'dimensions.dart';

const Color background = Color(0xFFF4F3F1);
const Color pinkBackground = Color(0xFFE8DFE2);
const Color pinkBackgroundDark = Color(0xFFE8D3D0);
const Color pinkBackgroundDark_75 = Color(0xBFE8D3D0);
const Color pinkBackgroundDark_50 = Color(0x7FE8D3D0);
const Color pinkBackgroundDark_25 = Color(0x3FE8D3D0);
const Color pinkBackgroundDark_15 = Color(0x26E8D3D0);
const Color pinkShadow = Color(0xFFBBAAB0);
const Color pinkPrimary = Color(0xFF8D6B75);

const Color greyBackground = Color(0xFFDDE0E1);
const Color greyBackgroundDark = Color(0xFFD2D9D7);
const Color greyShadow = Color(0xFF8D9BA0);
const Color greyPrimary = Color(0xFF506369);

const Color _error = Color(0xFFAC2E51);
// --- End Palette ---

final ThemeData pmTheme = ThemeData(
  useMaterial3: true,
  brightness: Brightness.light,

  colorScheme: ColorScheme(
    brightness: Brightness.light,

    primary: greyPrimary,
    onPrimary: background,
    primaryContainer: greyBackgroundDark,
    onPrimaryContainer: greyPrimary,

    secondary: pinkPrimary,
    onSecondary: background,
    secondaryContainer: pinkBackgroundDark,
    onSecondaryContainer: pinkPrimary,

    tertiary: greyShadow,
    onTertiary: background,
    tertiaryContainer: greyBackground,
    onTertiaryContainer: greyPrimary,

    background: background,
    onBackground: greyPrimary,

    surface: pinkBackground,
    onSurface: greyPrimary,

    surfaceVariant: pinkBackgroundDark,
    onSurfaceVariant: greyPrimary,

    error: _error,
    onError: background,

    outline: greyShadow,
    shadow: pinkShadow,
  ),

  textTheme: const TextTheme().apply(
    bodyColor: greyPrimary,
    displayColor: greyPrimary,
  ),

);


const lightOnDarkTextStyle = TextStyle(color: background);
const darkOnLightTextStyle = TextStyle(color: greyPrimary);
