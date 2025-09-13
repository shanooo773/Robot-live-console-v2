FROM node:20-alpine

# Install necessary dependencies
RUN apk add --no-cache git python3 py3-pip g++ make curl bash openssh-client

# Create theia user
RUN addgroup -g 1001 theia && \
    adduser -u 1001 -G theia -s /bin/bash -D theia

WORKDIR /home/theia
USER theia

# Create package.json with Theia 1.64.1 dependencies
RUN echo '{\
  "private": true,\
  "dependencies": {\
    "@theia/callhierarchy": "1.64.1",\
    "@theia/file-search": "1.64.1",\
    "@theia/markers": "1.64.1",\
    "@theia/messages": "1.64.1",\
    "@theia/mini-browser": "1.64.1",\
    "@theia/navigator": "1.64.1",\
    "@theia/outline-view": "1.64.1",\
    "@theia/plugin-ext-vscode": "1.64.1",\
    "@theia/preferences": "1.64.1",\
    "@theia/preview": "1.64.1",\
    "@theia/search-in-workspace": "1.64.1",\
    "@theia/terminal": "1.64.1",\
    "@theia/workspace": "1.64.1"\
  },\
  "devDependencies": {\
    "@theia/cli": "1.64.1"\
  },\
  "scripts": {\
    "prepare": "yarn run clean && yarn build && yarn run download:plugins",\
    "clean": "theia clean",\
    "build": "theia build --mode development",\
    "start": "theia start /home/project --hostname=0.0.0.0 --port=3000",\
    "download:plugins": "theia download:plugins"\
  },\
  "theiaPluginsDir": "plugins",\
  "theiaPlugins": {\
    "vscode-builtin-extensions-pack": "https://github.com/theia-ide/vscode-builtin-extensions/releases/download/v1.64.0/vscode-builtin-extensions-pack-v1.64.0.vsix",\
    "ms-python.python": "https://ms-python.gallery.vsassets.io/_apis/public/gallery/publisher/ms-python/extension/python/latest/assetbyname/Microsoft.VisualStudio.Code.Extension.vsix",\
    "ms-vscode.cpptools": "https://open-vsx.org/api/ms-vscode/cpptools/latest/file/ms-vscode.cpptools-latest.vsix"\

  }\
}' > package.json

# Install Theia
RUN yarn config set registry https://registry.npmjs.org \
 && npm config set registry https://registry.npmjs.org 
RUN yarn install --frozen-lockfile --network-timeout 600000 && \
    yarn run prepare && \
    yarn cache clean

# Create project directory
RUN mkdir -p /home/project

EXPOSE 3000

CMD ["yarn", "start"]
