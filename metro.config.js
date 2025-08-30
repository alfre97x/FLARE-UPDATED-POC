const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

module.exports = (() => {
  const config = getDefaultConfig(__dirname);
  
  // Add support for SVG files
  const { transformer, resolver } = config;
  
  config.transformer = {
    ...transformer,
    babelTransformerPath: require.resolve('react-native-svg-transformer'),
  };
  
  config.resolver = {
    ...resolver,
    assetExts: resolver.assetExts.filter(ext => ext !== 'svg'),
    sourceExts: [...resolver.sourceExts, 'svg'],
    // Add support for web-specific extensions
    platforms: [...resolver.platforms, 'web'],
    // Ensure proper resolution of modules
    extraNodeModules: {
      'app': path.resolve(__dirname),
      // Ensure React and React Native are resolved to a single instance
      'react': path.resolve(__dirname, 'node_modules/react'),
      'react-dom': path.resolve(__dirname, 'node_modules/react-dom'),
      'react-native': path.resolve(__dirname, 'node_modules/react-native'),
      'react-native-web': path.resolve(__dirname, 'node_modules/react-native-web'),
    },
  };
  
  return config;
})();
