import 'package:flutter/material.dart';
import 'package:amplify_auth_cognito/amplify_auth_cognito.dart';
import 'package:amplify_authenticator/amplify_authenticator.dart';
import 'package:amplify_flutter/amplify_flutter.dart';

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

class _TagSelectorExamplePageState extends State<TagSelectorExamplePage> {
  final List<String> _allAvailableTags = [
    'Flutter', 'Dart', 'Firebase', 'Productivity', 'Health',
    'Fitness', 'Groceries', 'Personal', 'Work',
  ];

  final Set<String> _currentTags = {'Flutter'};
  final _formKey = GlobalKey<FormState>();

  int _currentIndex = 0;

  late DateRange initialDateTime;
  late Set<String> initialTags;
  late String? initialText;

  @override
  void initState() {
    super.initState();

        initialTags = {'Health'};
        initialDateTime = DateRange.m1;
        initialText = "Initial Text";

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

  void _myOnChanged(Set<String> tags) {
    print('--- Tags Changed ---');
    print(tags);
  }

  Future _myOnNew(String newTag) async {
    print('--- New Tag Created ---');
    print(newTag);
    setState(() {
      _allAvailableTags.add(newTag);
    });
  }

  // --- 3. ADD A CALLBACK FOR THE FILTER ---
  void _onFilterChanged(String? text, DateRange range, Set<String>? tags) {
    setState(() {


      initialTags =tags ?? {};
      initialDateTime = range;
      initialText = text;


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

    try {
      return Scaffold(
        key: _scaffoldKey,

        appBar: AppBar(title: const Text('Tag Selector Example')), body: Form(
          key: _formKey, // 5. FIX: Point this to the _formKey
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                PredictedMeFilter(
                  initialDateTime: initialDateTime,
                  initialTags: initialTags,
                  initialText: initialText,
                  onCriteriaChanged: _onFilterChanged,
                  tagsSuggestionsProvider: _myTagsProvider,
                ),
                // This is your separate tag selector for testing
                PredictedMeTagsSelector(
                  initialTagNames: _currentTags,
                  tagsProvider: _myTagsProvider,
                  onChanged: _myOnChanged,
                  onNew: _myOnNew,
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: () {
                    _formKey.currentState?.validate();
                  },
                  child: const Text('Validate Form'),
                ),
              ],
            ),
          ),
        ),
        bottomNavigationBar: PredictedNavBar(
          navs: navItems,
          currentIndex: _currentIndex,
        ),
      );
    } catch (e) {
      showSnackBar(e.toString());
      return SizedBox.shrink();
    }
  }
}