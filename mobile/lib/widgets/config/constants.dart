

import 'package:flutter/material.dart';
const String empty = '';
class Dimensions {
  // Radii
  static const double borderRadiusSmall = 4.0;
  static const double borderRadiusMedium = 8.0;
  static const double borderRadiusLarge = 12.0;
  static const double borderRadiusExtraLarge = 20.0;
  // Padding & Spacing
  static const double paddingExtraSmall = 4.0;
  static const double paddingSmall = 8.0;
  static const double paddingMedium = 12.0;
  static const double paddingLarge = 24.0;
  static const double spacingSmall = 6.0;
  static const double spacingNone = 0.0;

  // Component Sizes
  static const double suggestionsMaxHeight = 150.0;
  static const double tagInputWidth = 150.0;

  // Icons & Text
  static const double iconSizeSmall = 15.0;
  static const double iconSizeMedium = 20.0;
  static const double iconSizeLarge = 25.0;

  static const double fontSizeSmall = 12.0;
  static const double fontSizeMedium = 15.0;


  // Elevation
  static const double elevationNone = 0.0;
  static const double elevationSmall = 2.0;
  static const double elevationMedium = 5.0;

  // Borders
  static const double borderWidthSmall = 1.5;

  // Opacity
  static const double opacitySmall = 0.2;
  static const double opacityMedium = 0.25;

  static const double sizedBoxExtraSmall = 4.0;
  static const double sizedBoxSmall = 10.0;
  static const double sizedBoxMedium = 15.0;
  static const double sizedBoxLarge = 20.0;
  static const double sizedBoxExtraLarge = 25.0;





  static const double borderExtraThin = 0.5;


}

const autocompleteAnimationMs = 1000;
const tagFieldLength = 500;

const fullScreenCoefficient = 0.9;
const halfScreenCoefficient = 0.5;
const quorterScreenCoefficient = 0.25;
double Function(BuildContext context) fullWidth = (BuildContext context) =>  MediaQuery.of(context).size.width * fullScreenCoefficient;
double Function(BuildContext context) halfWidth = (BuildContext context) =>  MediaQuery.of(context).size.width * halfScreenCoefficient;
double Function(BuildContext context) quoterWidth = (BuildContext context) =>  MediaQuery.of(context).size.width * quorterScreenCoefficient;

double Function(BuildContext context) fullHeight = (BuildContext context) =>  MediaQuery.of(context).size.height * fullScreenCoefficient;
double Function(BuildContext context) halfHeight = (BuildContext context) =>  MediaQuery.of(context).size.height * halfScreenCoefficient;
double Function(BuildContext context) quoterHeight = (BuildContext context) =>  MediaQuery.of(context).size.height * quorterScreenCoefficient;


const msInSec = 1000;