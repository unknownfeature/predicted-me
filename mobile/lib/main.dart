import 'package:flutter/material.dart';
import 'package:amplify_auth_cognito/amplify_auth_cognito.dart';
import 'package:amplify_authenticator/amplify_authenticator.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:flutter/rendering.dart';
import 'package:pm/widgets/config/constants.dart';

import 'package:pm/widgets/config/theme.dart';
import 'package:pm/widgets/pm_nav_bar.dart';
import 'package:pm/widgets/pm_tags_selector.dart';
import 'package:pm/widgets/pm_filter.dart';
final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

void showSnackBar(String message) {
  ScaffoldMessenger.of(
    _scaffoldKey.currentContext!,
  ).showSnackBar(SnackBar(content: Text(message)));
}

void main() {
  runApp(const PredictedMe());
}

class PredictedMe extends StatefulWidget {
  const PredictedMe({Key? key}) : super(key: key);

  @override
  State<PredictedMe> createState() => _PredictedMeState();
}

class _PredictedMeState extends State<PredictedMe> {
  @override
  void initState() {
    super.initState();
    _configureAmplify();
  }

  void _configureAmplify() async {
    try {
      await Amplify.addPlugin(AmplifyAuthCognito());
      // await Amplify.addPlugin(AmplifyPushNotificationsPinpoint());
      await Amplify.configure('''{
  "UserAgent": "aws-amplify-cli/2.0",
  "Version": "1.0",
  "auth": {
    "plugins": {
      "IdentityManager": {
              "Default": {}
            },
      "awsCognitoAuthPlugin": {
        "CognitoUserPool": {
          "Default": {
            "PoolId": "<pool>",
            "AppClientId": "<client>",
            "Region": "us-east-1"
          }
        },
        "Auth": { 
          "Default": {
            "authenticationFlowType": "USER_SRP_AUTH",
            "usernameAttributes": [
              "email"
            ],
            "signupAttributes": [
              "email"
            ],
            "passwordProtectionSettings": {
              "passwordPolicyMinLength": 8,
              "passwordPolicyCharacters": [
                "REQUIRES_NUMBERS",
                "REQUIRES_SYMBOLS",
                "REQUIRES_UPPERCASE",
                "REQUIRES_UPPERCASE"
              ]
            },
            "mfaConfiguration": "ON"
          }
        }
      }
    }
  }
}''');
      print('Successfully configured');
    } on Exception catch (e) {
      print('Error configuring Amplify: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Authenticator(
      child: MaterialApp(theme: pmTheme, home: TagSelectorExamplePage()),
    );
  }
}

class TagSelectorExamplePage extends StatefulWidget {
  const TagSelectorExamplePage({Key? key}) : super(key: key);

  @override
  _TagSelectorExamplePageState createState() => _TagSelectorExamplePageState();
}

class _TagSelectorExamplePageState extends State<TagSelectorExamplePage>
    with TickerProviderStateMixin {
  final List<String> _allAvailableTags = [
    'Flutter', 'Dart', 'Firebase', 'Productivity', 'Health',
    'Fitness', 'Groceries', 'Personal', 'Work',
  ];
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  int _currentIndex = 0;
  late DateRange _currentDateRange;
  late Set<String> _currentTags;
  late String? _currentText;

  // --- Animation and Scroll Controllers ---
  late final AnimationController _slideController;
  late final Animation<Offset> _slideAnimation;
  late final ScrollController _scrollController;

  @override
  void initState() {
    super.initState();
    _currentTags = {'Health'};
    _currentDateRange = DateRange.m1;
    _currentText = "Initial Text";

    // --- Initialize Controllers ---
    _scrollController = ScrollController();
    _scrollController.addListener(_handleScroll);

    _slideController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 250),
    );

    _slideAnimation = Tween<Offset>(
      begin: Offset.zero,
      end: const Offset(0, -1.0), // Slide up (off-screen)
    ).animate(CurvedAnimation(
      parent: _slideController,
      curve: Curves.fastOutSlowIn,
    ));
  }

  @override
  void dispose() {
    _scrollController.removeListener(_handleScroll);
    _scrollController.dispose();
    _slideController.dispose();
    super.dispose();
  }

  void _handleScroll() {
    final direction = _scrollController.position.userScrollDirection;
    if (direction == ScrollDirection.reverse) {
      _slideController.forward(); // Hide
    } else if (direction == ScrollDirection.forward) {
      _slideController.reverse(); // Show
    }
  }

  void _onNavTapped(int index) {
    setState(() {
      _currentIndex = index;
    });
    print('Tapped index $index');
  }

  Future<Iterable<String>> _myTagsProvider(String query) async {
    if (query.isEmpty) {
      return Future.value(const Iterable.empty());
    }
    await Future.delayed(Duration(milliseconds: 100)); // Simulate network
    return _allAvailableTags.where(
          (tag) => tag.toLowerCase().contains(query.toLowerCase()),
    ).take(10);
  }

  void _onFilterChanged(String? text, DateRange range, Set<String>? tags) {
    setState(() {
      _currentText = text;
      _currentDateRange = range;
      _currentTags = tags ?? {};
    });
    print('--- FILTER CRITERIA UPDATED ---');
    print('Text: $text, Range: ${range.toDisplayString}, Tags: $tags');
  }

  @override
  Widget build(BuildContext context) {
    final List<Nav> navItems = [
      Nav("Home", Icons.home_outlined, () => _onNavTapped(0)),
      Nav("Search", Icons.search, () => _onNavTapped(1)),
      Nav("Add", Icons.add_circle_outline, () => _onNavTapped(2)),
      Nav("Profile", Icons.person_outline, () => _onNavTapped(3)),
      Nav("Note", Icons.note_alt_outlined, () => _onNavTapped(4)),
    ];

    return Scaffold(
      key: _scaffoldKey,

      // --- The Body is now a Stack ---
      body: Stack(
        children: [
          // --- Child 1: The Scrollable Content ---
          CustomScrollView(
            controller: _scrollController,
            slivers: [
              // This dummy sliver adds space at the top so the list
              // starts below the collapsed filter bar.
              SliverPadding(
                padding: const EdgeInsets.only(top: kToolbarHeight + Dimensions.paddingMedium * 2),
                sliver: SliverList(
                  delegate: SliverChildBuilderDelegate(
                        (BuildContext context, int index) {
                      return ListTile(
                        title: Text('Search Result Item $index'),
                        subtitle: Text(
                          'Based on: text: "${_currentText ?? ''}", '
                              'range: ${_currentDateRange.toDisplayString}, ',
                        ),
                      );
                    },
                    childCount: 50,
                  ),
                ),
              ),
            ],
          ),

          // --- Child 2: The Animated, Floating Filter Bar ---
          SlideTransition(
            position: _slideAnimation,
            child: PredictedMeFilter(
              initialDateTime: _currentDateRange,
              initialTags: _currentTags,
              initialText: _currentText,
              onCriteriaChanged: _onFilterChanged,
              tagsSuggestionsProvider: _myTagsProvider,
            ),
          ),
        ],
      ),
      bottomNavigationBar: PredictedNavBar(
        navs: navItems,
        currentIndex: _currentIndex,
      ),
    );
  }
}