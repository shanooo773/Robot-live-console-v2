FROM node:18-alpine

# Install necessary dependencies
RUN apk add --no-cache \
    git \
    python3 \
    py3-pip \
    g++ \
    make \
    curl \
    bash \
    openssh-client

# Create theia user
RUN addgroup -g 1001 theia && \
    adduser -u 1001 -G theia -s /bin/bash -D theia

# Install Theia and extensions
WORKDIR /home/theia
USER theia

# Create package.json for Theia
RUN echo '{\
  "private": true,\
  "dependencies": {\
    "@theia/callhierarchy": "1.42.0",\
    "@theia/file-search": "1.42.0",\
    "@theia/git": "1.42.0",\
    "@theia/markers": "1.42.0",\
    "@theia/messages": "1.42.0",\
    "@theia/mini-browser": "1.42.0",\
    "@theia/navigator": "1.42.0",\
    "@theia/outline-view": "1.42.0",\
    "@theia/plugin-ext-vscode": "1.42.0",\
    "@theia/preferences": "1.42.0",\
    "@theia/preview": "1.42.0",\
    "@theia/search-in-workspace": "1.42.0",\
    "@theia/terminal": "1.42.0",\
    "@theia/workspace": "1.42.0",\
    "@theia/cpp": "1.42.0"\
  },\
  "devDependencies": {\
    "@theia/cli": "1.42.0"\
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
    "vscode-builtin-extensions-pack": "https://github.com/theia-ide/vscode-builtin-extensions/releases/download/v1.39.1-prel/vscode-builtin-extensions-pack-v1.39.1-prel.vsix",\
    "ms-python.python": "https://ms-python.gallery.vsassets.io/_apis/public/gallery/publisher/ms-python/extension/python/latest/assetbyname/Microsoft.VisualStudio.Code.Extension.vsix"\
  }\
}' > package.json


# Install Theia
RUN yarn install --frozen-lockfile && \
    yarn run prepare && \
    yarn cache clean

# Create project directory
RUN mkdir -p /home/project

# Expose port
EXPOSE 3000

# Start Theia
CMD ["yarn", "start"]
