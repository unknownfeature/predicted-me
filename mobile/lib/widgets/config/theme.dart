import 'package:flutter/material.dart';
import 'dimensions.dart';

const Color _background = Color(0xFFF4F3F1);
const Color _pinkBackground = Color(0xFFE8DFE2);
const Color _pinkBackgroundDark = Color(0xFFE8D3D0);
const Color _pinkShadow = Color(0xFFBBAAB0);
const Color _pinkPrimary = Color(0xFF8D6B75);

const Color _greyBackground = Color(0xFFDDE0E1);
const Color _greyBackgroundDark = Color(0xFFD2D9D7);
const Color _greyShadow = Color(0xFF8D9BA0);
const Color _greyPrimary = Color(0xFF506369);

const Color _error = Color(0xFFAC2E51);
// --- End Palette ---

final ThemeData pmTheme = ThemeData(
  useMaterial3: true,
  brightness: Brightness.light,

  colorScheme: ColorScheme(
    brightness: Brightness.light,

    primary: _greyPrimary,
    onPrimary: _background,
    primaryContainer: _greyBackgroundDark,
    onPrimaryContainer: _greyPrimary,

    secondary: _pinkPrimary,
    onSecondary: _background,
    secondaryContainer: _pinkBackgroundDark,
    onSecondaryContainer: _pinkPrimary,

    tertiary: _greyShadow,
    onTertiary: _background,
    tertiaryContainer: _greyBackground,
    onTertiaryContainer: _greyPrimary,

    background: _background,
    onBackground: _greyPrimary,

    surface: _pinkBackground,
    onSurface: _greyPrimary,

    surfaceVariant: _pinkBackgroundDark,
    onSurfaceVariant: _greyPrimary,

    error: _error,
    onError: _background,

    outline: _greyShadow,
    shadow: _pinkShadow,
  ),

  textTheme: const TextTheme().apply(
    bodyColor: _greyPrimary,
    displayColor: _greyPrimary,
  ),

  appBarTheme: const AppBarTheme(
    backgroundColor: _greyPrimary,
    foregroundColor: _background,
    elevation: Dimensions.elevationNone,
    centerTitle: true,
  ),

  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: _greyPrimary,
      foregroundColor: _background,
      shadowColor: _pinkShadow.withOpacity(Dimensions.opacityMedium),
      elevation: Dimensions.elevationMedium,
      shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Dimensions.borderRadiusMedium)),
      padding: const EdgeInsets.symmetric(
          horizontal: Dimensions.paddingLarge,
          vertical: Dimensions.paddingMedium),
    ),
  ),

  textButtonTheme: TextButtonThemeData(
    style: TextButton.styleFrom(
      foregroundColor: _pinkPrimary,
    ),
  ),

  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: _pinkPrimary,
      side: const BorderSide(
          color: _pinkPrimary, width: Dimensions.borderWidthSmall),
      shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Dimensions.borderRadiusMedium)),
      padding: const EdgeInsets.symmetric(
          horizontal: Dimensions.paddingLarge,
          vertical: Dimensions.paddingMedium),
    ),
  ),

  cardTheme: CardThemeData(
    color: _pinkBackground,
    surfaceTintColor: Colors.transparent,
    elevation: Dimensions.elevationSmall,
    shadowColor: _pinkShadow.withOpacity(Dimensions.opacitySmall),
    shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(Dimensions.borderRadiusLarge)),
  ),

  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: _greyBackground,
    hintStyle: const TextStyle(color: _greyShadow),
    border: InputBorder.none,
    enabledBorder: InputBorder.none,
    focusedBorder: InputBorder.none,
  ),
);