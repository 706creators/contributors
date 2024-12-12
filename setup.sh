#!/bin/bash

# Create directory structure
mkdir -p profiles data dist scripts/components

# Create package.json
cat > package.json << 'EOF'
{
  "name": "github-contributor-sites",
  "type": "module",
  "version": "1.0.0",
  "description": "Generate static sites for GitHub contributors",
  "scripts": {
    "build": "node scripts/build.js",
    "generate": "node dist/generate_site.js"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "recharts": "^2.12.0"
  },
  "devDependencies": {
    "esbuild": "^0.19.8"
  }
}
EOF

# Create ContributorProfile.js
cat > scripts/components/ContributorProfile.js << 'EOF'
import React, { useState } from 'react';

const ActivitySection = ({ title, items = [], color = 'text-blue-500' }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  return React.createElement('div', { className: 'border rounded-lg p-4' },
    React.createElement('div', {
      className: 'flex items-center justify-between cursor-pointer',
      onClick: toggleExpand
    },
      React.createElement('h3', { className: 'font-semibold' }, title),
      React.createElement('span', null, isExpanded ? '▼' : '▶')
    ),
    isExpanded && React.createElement('div', { className: 'mt-4 space-y-2' },
      items.map((item, index) => 
        React.createElement('div', { key: index, className: 'p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded' },
          React.createElement('a', {
            href: item.url,
            target: '_blank',
            rel: 'noopener noreferrer',
            className: 'text-sm hover:text-blue-500 flex flex-col gap-1'
          },
            React.createElement('span', { className: 'font-medium' }, 
              item.message || item.title || item.body
            ),
            React.createElement('span', { className: 'text-gray-500 text-xs' },
              new Date(item.date || item.created_at).toLocaleDateString()
            )
          )
        )
      )
    )
  );
};

const StatCard = ({ name, value }) => {
  return React.createElement('div', { className: 'bg-white dark:bg-gray-800 rounded-lg p-6 shadow' },
    React.createElement('h3', { className: 'font-semibold' }, name),
    React.createElement('p', { className: 'text-2xl font-bold' }, value)
  );
};

const ContributorProfile = ({ data }) => {
  const stats = [
    { name: 'Commits', value: data.activity.code.total_commits },
    { name: 'PRs', value: data.activity.code.total_prs },
    { name: 'Issues', value: data.activity.issues.total_opened },
    { name: 'Comments', value: data.activity.engagement.total_comments }
  ];

  return React.createElement('div', { className: 'max-w-7xl mx-auto p-4 space-y-6' },
    React.createElement('div', { className: 'bg-white dark:bg-gray-800 rounded-lg p-6 shadow' },
      React.createElement('div', { className: 'flex items-center gap-4' },
        React.createElement('img', {
          src: data.avatar_url,
          alt: `${data.username}'s avatar`,
          className: 'w-16 h-16 rounded-full'
        }),
        React.createElement('div', null,
          React.createElement('h1', { className: 'text-2xl font-bold' }, data.username),
          React.createElement('p', { className: 'text-gray-600 dark:text-gray-400' },
            `${data.total_contributions} total contributions`
          )
        )
      )
    ),

    React.createElement('div', { className: 'grid grid-cols-1 md:grid-cols-4 gap-4' },
      stats.map(stat => React.createElement(StatCard, { key: stat.name, ...stat }))
    ),

    React.createElement('div', { className: 'space-y-4' },
      React.createElement(ActivitySection, {
        title: 'Commits',
        items: data.activity.code.commits
      }),
      React.createElement(ActivitySection, {
        title: 'Pull Requests',
        items: data.activity.code.pull_requests
      }),
      React.createElement(ActivitySection, {
        title: 'Issues',
        items: data.activity.issues.opened || []
      }),
      React.createElement(ActivitySection, {
        title: 'Comments',
        items: [
          ...(data.activity.engagement.issue_comments || []),
          ...(data.activity.engagement.pr_comments || [])
        ]
      })
    )
  );
};

export default ContributorProfile;
EOF

# Create build.js
cat > scripts/build.js << 'EOF'
import * as esbuild from 'esbuild';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);

const externals = [
  'react',
  'react-dom',
  'react-dom/server',
  'recharts',
  'fs',
  'path',
  'url',
  'stream',
  'util',
  'http',
  'zlib'
];

await esbuild.build({
  entryPoints: ['scripts/generate_site.js'],
  bundle: true,
  platform: 'node',
  target: 'node18',
  format: 'esm',
  outfile: 'dist/generate_site.js',
  external: externals,
  define: {
    'process.env.NODE_ENV': '"production"'
  }
});

console.log('Build complete');
EOF

# Create generate_site.js
cat > scripts/generate_site.js << 'EOF'
import React from 'react';
import { renderToString } from 'react-dom/server';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import ContributorProfile from './components/ContributorProfile.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const template = (content, data) => `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${data.username} - GitHub Contributions</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-50 dark:bg-gray-900">
    <div id="root">${content}</div>
    <script>
        window.__DATA__ = ${JSON.stringify(data)};
    </script>
    <script type="text/javascript">
        const ActivitySection = ({ title, items = [], color = 'text-blue-500' }) => {
            const [isExpanded, setIsExpanded] = React.useState(false);
            
            return React.createElement('div', { className: 'border rounded-lg p-4' },
                React.createElement('div', {
                    className: 'flex items-center justify-between cursor-pointer',
                    onClick: () => setIsExpanded(!isExpanded)
                },
                    React.createElement('h3', { className: 'font-semibold' }, title),
                    React.createElement('span', null, isExpanded ? '▼' : '▶')
                ),
                isExpanded && React.createElement('div', { className: 'mt-4 space-y-2' },
                    items.map((item, index) => 
                        React.createElement('div', { key: index, className: 'p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded' },
                            React.createElement('a', {
                                href: item.url,
                                target: '_blank',
                                rel: 'noopener noreferrer',
                                className: 'text-sm hover:text-blue-500 flex flex-col gap-1'
                            },
                                React.createElement('span', { className: 'font-medium' }, 
                                    item.message || item.title || item.body
                                ),
                                React.createElement('span', { className: 'text-gray-500 text-xs' },
                                    new Date(item.date || item.created_at).toLocaleDateString()
                                )
                            )
                        )
                    )
                )
            );
        };

        const StatCard = ({ name, value }) => {
            return React.createElement('div', { className: 'bg-white dark:bg-gray-800 rounded-lg p-6 shadow' },
                React.createElement('h3', { className: 'font-semibold' }, name),
                React.createElement('p', { className: 'text-2xl font-bold' }, value)
            );
        };

        const ContributorProfile = ({ data }) => {
            const stats = [
                { name: 'Commits', value: data.activity.code.total_commits },
                { name: 'PRs', value: data.activity.code.total_prs },
                { name: 'Issues', value: data.activity.issues.total_opened },
                { name: 'Comments', value: data.activity.engagement.total_comments }
            ];

            return React.createElement('div', { className: 'max-w-7xl mx-auto p-4 space-y-6' },
                React.createElement('div', { className: 'bg-white dark:bg-gray-800 rounded-lg p-6 shadow' },
                    React.createElement('div', { className: 'flex items-center gap-4' },
                        React.createElement('img', {
                            src: data.avatar_url,
                            alt: \`\${data.username}'s avatar\`,
                            className: 'w-16 h-16 rounded-full'
                        }),
                        React.createElement('div', null,
                            React.createElement('h1', { className: 'text-2xl font-bold' }, data.username),
                            React.createElement('p', { className: 'text-gray-600 dark:text-gray-400' },
                                \`\${data.total_contributions} total contributions\`
                            )
                        )
                    )
                ),

                React.createElement('div', { className: 'grid grid-cols-1 md:grid-cols-4 gap-4' },
                    stats.map(stat => React.createElement(StatCard, { key: stat.name, ...stat }))
                ),

                React.createElement('div', { className: 'space-y-4' },
                    React.createElement(ActivitySection, {
                        title: 'Commits',
                        items: data.activity.code.commits
                    }),
                    React.createElement(ActivitySection, {
                        title: 'Pull Requests',
                        items: data.activity.code.pull_requests
                    }),
                    React.createElement(ActivitySection, {
                        title: 'Issues',
                        items: data.activity.issues.opened || []
                    }),
                    React.createElement(ActivitySection, {
                        title: 'Comments',
                        items: [
                            ...(data.activity.engagement.issue_comments || []),
                            ...(data.activity.engagement.pr_comments || [])
                        ]
                    })
                )
            );
        };

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(React.createElement(ContributorProfile, { data: window.__DATA__ }));
    </script>
</body>
</html>`;

const generateSite = async () => {
    const inputDir = path.join(path.dirname(__dirname), 'data');
    const outputDir = path.join(path.dirname(__dirname), 'profiles');

    try {
        await fs.mkdir(outputDir, { recursive: true });
        const files = await fs.readdir(inputDir);
        const jsonFiles = files.filter(file => file.endsWith('.json'));

        // Load all contributor data and sort by total contributions
        const contributorsData = await Promise.all(
            jsonFiles.map(async (file) => {
                const data = JSON.parse(
                    await fs.readFile(path.join(inputDir, file), 'utf-8')
                );
                return data;
            })
        );

        // Sort contributors by total contributions
        contributorsData.sort((a, b) => b.total_contributions - a.total_contributions);

        // Generate individual profile pages
        for (const data of contributorsData) {
            const content = renderToString(
                React.createElement(ContributorProfile, { data })
            );
            
            const html = template(content, data);
            
            await fs.writeFile(
                path.join(outputDir, `${data.username}.html`),
                html
            );
            
            console.log(`Generated profile for ${data.username}`);
        }

        // Generate index.html with sorted contributors
        const indexContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub Contributors</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-50 dark:bg-gray-900">
    <div class="max-w-7xl mx-auto p-8">
        <h1 class="text-3xl font-bold mb-8 text-gray-900 dark:text-white">GitHub Contributors</h1>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            ${contributorsData.map(data => `
                <a href="${data.username}.html" 
                   class="block p-6 bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-shadow">
                    <div class="flex items-center gap-4">
                        <img src="${data.avatar_url}" 
                             alt="${data.username}" 
                             class="w-12 h-12 rounded-full">
                        <div>
                            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">${data.username}</h2>
                            <p class="text-gray-600 dark:text-gray-400">
                                ${data.total_contributions} contributions
                            </p>
                        </div>
                    </div>
                </a>
            `).join('')}
        </div>
    </div>
</body>
</html>`;

        await fs.writeFile(path.join(outputDir, 'index.html'), indexContent);

        console.log('Site generation complete! Open ./profiles/index.html to view the result.');
    } catch (error) {
        console.error('Error generating site:', error);
        console.error(error.stack);
    }
};

generateSite();
EOF

# Make the script executable
chmod +x scripts/build.js

# Create README
cat > README.md << 'EOF'
# GitHub Contributor Sites Generator

Generate static sites showing GitHub contributor activity.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Put your contributor data JSON files in the `data` directory

3. Build and generate the site:
```bash
npm run build
npm run generate
```

4. Open `profiles/index.html` to view the result

## Directory Structure

- `data/` - Place contributor JSON files here
- `scripts/` - Source code
- `dist/` - Built files
- `profiles/` - Generated static site

## Scripts

- `npm run build` - Bundle the site generator
- `npm run generate` - Generate the static site
EOF

# Initialize git repository
git init
echo "node_modules/\ndist/" > .gitignore

# Initialize npm project
npm install

echo "Setup complete! Please add your contributor data JSON files to the 'data' directory."
echo "Then run: npm run build && npm run generate"
