# Wind farm design software developed on more than 30 years of expertise
        
[Online Knowledge Base](https://github.com/Underwriters-Labs/renewables.openwind.help/wiki)
    
![image](https://github.com/user-attachments/assets/17195e17-79f5-4e6d-a30a-351456cb2a3e)

Openwind is a wind farm design and optimization software used throughout a wind project’s development to create optimal turbine layouts that maximize energy production, minimize energy losses, account for plant development costs and generate overall project efficiencies.

Our software was developed by drawing on more than 30 years of advisory expertise, which has helped ensure that stakeholders involved in wind project development around the world have confidence in our platform. Additionally, Openwind’s compatibility with other computer wind programs enables you to seamlessly share files and easily migrate existing procedures into our software.

# Static Open Wind Help website. 
Static  website generated with hugo from this repos github Wiki.
## Development: 
### Requirements: 
 - Python (3.13.9)
 - Hugo (0.152.2)
## Steps to re-generate the static site: 
1. copy the contents of the Open wind Wiki into the `website/content` folder.
2. Run the orchestration script to process all content:
   ```bash
   python website/tools/run_all_tools.py --base website --backup
   ```
   This runs all processing steps in sequence:
   - [Add Empty FrontMatter](website/tools/add_empty_frontmatter.py) — ensures all .md files have YAML frontmatter
   - [Convert Wiki Links](website/tools/convert_wiki_links.py) — converts `[[File Name]]` to `[Display Name](/file-name)` (lowercased)
   - [Download Images](website/tools/download_images.py) — downloads external images and updates links to serve locally
   - [Generate Search Index](website/tools/generate_search_index.py) — regenerates the search index

   **Available Flags:**
   - `--base PATH` — specify the base path (default: `website`)
   - `--dry-run` — preview what would happen without making any changes to files
   - `--backup` — create `.bak` backup copies of files before modifying originals
   - `--skip-frontmatter` — skip the frontmatter addition step
   - `--skip-wiki-links` — skip the wiki link conversion step
   - `--skip-images` — skip the image download step
   - `--skip-search` — skip the search index regeneration step

3. run the `hugo` Command.

4. Publish/serve the `website/public` directory.

### Useful Commands:  ( use within `website` directory.)
1. `hugo --minify --cleanDestinationDir` - Builds the website. empties the `public` dir and copies a minified version of the files into it. 
2. `hugo serve --noHTTPCache  --disableFastRender -w` - Development server. 
