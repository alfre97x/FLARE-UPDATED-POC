/**
 * Main App component wrapper
 * This file ensures proper React initialization for both web and native environments
 */

import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';

// Import screens directly to avoid nested App component issues
import HomeScreen from './space-data-app/screens/HomeScreen';
import DataSelectionScreen from './space-data-app/screens/DataSelectionScreen';
import PaymentScreen from './space-data-app/screens/PaymentScreen';
import ResultsScreen from './space-data-app/screens/ResultsScreen';

// Create the stack navigator
const Stack = createNativeStackNavigator();

// Create a class component to avoid hooks issues
class App extends React.Component {
  render() {
    return (
      <SafeAreaProvider>
        <NavigationContainer>
          <Stack.Navigator initialRouteName="Home">
            <Stack.Screen 
              name="Home" 
              component={HomeScreen} 
              options={{ title: 'Space Data Purchase' }}
            />
            <Stack.Screen 
              name="DataSelection" 
              component={DataSelectionScreen} 
              options={{ title: 'Select Data' }}
            />
            <Stack.Screen 
              name="Payment" 
              component={PaymentScreen} 
              options={{ title: 'Payment' }}
            />
            <Stack.Screen 
              name="Results" 
              component={ResultsScreen} 
              options={{ title: 'Your Data' }}
            />
          </Stack.Navigator>
        </NavigationContainer>
        <StatusBar style="auto" />
      </SafeAreaProvider>
    );
  }
}

export default App;
