module.exports = function (jsModule) {
    switch (jsModule) {
        case 'drivelist': return require('/home/shayan/Robot-live-console-v2/theia/node_modules/drivelist/build/Release/drivelist.node');
    }
    throw new Error(`unhandled module: "${jsModule}"`);
}