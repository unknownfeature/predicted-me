
import 'package:flutter/material.dart';
import 'package:amplify_auth_cognito/amplify_auth_cognito.dart';
import 'package:amplify_authenticator/amplify_authenticator.dart';
import 'package:amplify_flutter/amplify_flutter.dart';

import 'package:pm/widgets/config/theme.dart';
import 'package:pm/widgets/pm_tags_selector.dart';

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
      child: MaterialApp(theme: pmTheme,  home: TagSelectorExamplePage()),
    );
  }
}

class TagSelectorExamplePage extends StatefulWidget {
  const TagSelectorExamplePage({Key? key}) : super(key: key);

  @override
  _TagSelectorExamplePageState createState() => _TagSelectorExamplePageState();
}

class _TagSelectorExamplePageState extends State<TagSelectorExamplePage> {
  // This is your pre-initialized list of tags
  final List<String> _allAvailableTags = [
    'Flutter',
    'Dart',
    'Firebase',
    'Productivity',
    'Health',
    'Fitness',
    'Groceries',
    'Personal',
    'Work',
  ];

  // This holds the currently selected tags
  final Set<String> _currentTags = {'Flutter'};
  final _formKey = GlobalKey<FormState>();

  /// This function is passed to the widget to provide suggestions
  Iterable<String> _myTagsProvider(String query) {
    if (query.isEmpty) {
      return const Iterable.empty();
    }
    // Filter the list based on the user's typing
    return _allAvailableTags.where(
      (tag) => tag.toLowerCase().contains(query.toLowerCase()),
    );
  }

  /// This function is passed to the widget to handle changes
  void _myOnChanged(Set<String> tags) {
    print('--- Tags Changed ---');
    print(tags);
  }

  /// This function is passed to the widget to handle new tag creation
  void _myOnNew(String newTag) {
    print('--- New Tag Created ---');
    print(newTag);
    // Add the new tag to your master list
    setState(() {
      _allAvailableTags.add(newTag);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Tag Selector Example')),
      body: Form(
        key: _formKey,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              // --- THIS IS YOUR WIDGET ---
              PredictedMeTagsSelectorWidget(
                initialTagNames: _currentTags,
                tagsProvider: _myTagsProvider,
                onChanged: _myOnChanged,
                onNew: _myOnNew,
              ),

              // --- END WIDGET ---
              const SizedBox(height: 20),

              ElevatedButton(
                onPressed: () {
                  // This will trigger the validator
                  _formKey.currentState?.validate();
                },
                child: const Text('Validate Form'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
