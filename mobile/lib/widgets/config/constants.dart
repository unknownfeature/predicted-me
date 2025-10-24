import 'package:flutter/material.dart';

const String empty = '';

const double borderRadiusSmall = 4.0;
const double borderRadiusMedium = 8.0;
const double borderRadiusLarge = 12.0;
const double borderRadiusExtraLarge = 20.0;
const double paddingExtraSmall = 4.0;
const double paddingSmall = 8.0;
const double paddingMedium = 12.0;
const double paddingLarge = 24.0;
const double spacingSmall = 6.0;
const double spacingNone = 0.0;

const double suggestionsMaxHeight = 150.0;
const double tagInputWidth = 150.0;

const double iconSizeSmall = 15.0;
const double iconSizeMedium = 20.0;
const double iconSizeLarge = 25.0;

const double fontSizeSmall = 12.0;
const double fontSizeMedium = 15.0;

const double elevationNone = 0.0;
const double elevationSmall = 2.0;
const double elevationMedium = 5.0;
const double elevationLarge = 10.0;

const double borderWidthSmall = 1.5;

// Opacity
const double opacitySmall = 0.2;
const double opacityMedium = 0.25;

const double sizedBoxExtraSmall = 4.0;
const double sizedBoxSmall = 10.0;
const double sizedBoxMedium = 15.0;
const double sizedBoxLarge = 20.0;
const double sizedBoxExtraLarge = 25.0;

const double borderExtraThin = 0.5;

const animationDuration = Duration(milliseconds: 1000);
const tagFieldLength = 500;

const fullScreenCoefficient = 0.9;
const halfScreenCoefficient = 0.5;
const quorterScreenCoefficient = 0.25;

double Function(BuildContext context) fullWidth = (BuildContext context) =>
    MediaQuery.of(context).size.width * fullScreenCoefficient;
double Function(BuildContext context) halfWidth = (BuildContext context) =>
    MediaQuery.of(context).size.width * halfScreenCoefficient;
double Function(BuildContext context) quoterWidth = (BuildContext context) =>
    MediaQuery.of(context).size.width * quorterScreenCoefficient;

double Function(BuildContext context) fullHeight = (BuildContext context) =>
    MediaQuery.of(context).size.height * fullScreenCoefficient;
double Function(BuildContext context) halfHeight = (BuildContext context) =>
    MediaQuery.of(context).size.height * halfScreenCoefficient;
double Function(BuildContext context) quoterHeight = (BuildContext context) =>
    MediaQuery.of(context).size.height * quorterScreenCoefficient;


const sigmaX = 10.0;
const sigmaY = 10.0;
