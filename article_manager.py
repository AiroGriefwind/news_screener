import streamlit as st
from datetime import datetime
from streamlit_sortables import sort_items

# Configure page
st.set_page_config(
    page_title="Article Sequence Manager",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Define location display order
LOCATION_ORDER = ['United States', 'Russia', 'Europe', 'Middle East', 'Southeast Asia', 'Japan', 'Korea', 'China', 'Others', 'Tech News']

# Initialize session state
if 'articles' not in st.session_state:
    # Create pseudo articles
    st.session_state.articles = {
        'United States': [
            {
                'id': 'us_1',
                'title': 'Biden Administration Announces New Infrastructure Plan',
                'content': 'The Biden administration today unveiled a comprehensive $2 trillion infrastructure package aimed at modernizing America\'s roads, bridges, and digital networks. The plan includes significant investments in renewable energy and electric vehicle charging stations.',
                'timestamp': '2025-08-19 14:30:00',
                'source': 'Reuters'
            },
            {
                'id': 'us_2',
                'title': 'Federal Reserve Signals Potential Rate Cut',
                'content': 'Federal Reserve officials indicated in recent statements that they may consider cutting interest rates in response to cooling inflation data. The decision could impact mortgage rates and consumer spending patterns.',
                'timestamp': '2025-08-19 13:15:00',
                'source': 'Bloomberg'
            }
        ],
        'China': [
            {
                'id': 'cn_1',
                'title': 'China\'s Economy Shows Signs of Recovery',
                'content': 'Recent economic indicators suggest China\'s economy is rebounding from previous slowdowns, with manufacturing PMI rising to 52.1 and consumer confidence improving across major cities.',
                'timestamp': '2025-08-19 12:45:00',
                'source': 'Xinhua'
            },
            {
                'id': 'cn_2',
                'title': 'Beijing Launches New Belt and Road Initiative Projects',
                'content': 'China announced new infrastructure projects under the Belt and Road Initiative, focusing on digital connectivity and sustainable development across Southeast Asian partner countries.',
                'timestamp': '2025-08-19 11:20:00',
                'source': 'South China Morning Post'
            }
        ],
        'Tech News': [
            {
                'id': 'tech_1',
                'title': 'OpenAI Announces GPT-5 Development Milestone',
                'content': 'OpenAI revealed significant progress in GPT-5 development, with enhanced reasoning capabilities and improved factual accuracy. The model is expected to launch in Q2 2026.',
                'timestamp': '2025-08-19 15:00:00',
                'source': 'TechCrunch'
            },
            {
                'id': 'tech_2',
                'title': 'Apple Unveils Revolutionary AR Glasses',
                'content': 'Apple\'s highly anticipated AR glasses feature advanced display technology and seamless integration with iOS ecosystem. The device promises to transform how users interact with digital content.',
                'timestamp': '2025-08-19 14:45:00',
                'source': 'The Verge'
            }
        ],
        'Europe': [
            {
                'id': 'eu_1',
                'title': 'EU Parliament Passes Landmark AI Regulation',
                'content': 'The European Parliament approved comprehensive AI regulation that sets global standards for artificial intelligence development and deployment, emphasizing transparency and ethical considerations.',
                'timestamp': '2025-08-19 10:30:00',
                'source': 'BBC'
            }
        ],
        'Middle East': [
            {
                'id': 'me_1',
                'title': 'UAE Announces Major Renewable Energy Investment',
                'content': 'The United Arab Emirates committed $50 billion toward renewable energy projects over the next decade, aiming to achieve carbon neutrality by 2050.',
                'timestamp': '2025-08-19 09:15:00',
                'source': 'Al Jazeera'
            }
        ],
        'Southeast Asia': [
            {
                'id': 'sea_1',
                'title': 'ASEAN Summit Focuses on Economic Cooperation',
                'content': 'Leaders from ASEAN member countries gathered to discuss enhanced economic cooperation and regional trade agreements, with emphasis on digital transformation initiatives.',
                'timestamp': '2025-08-19 08:45:00',
                'source': 'Channel NewsAsia'
            }
        ],
        'Others': [
            {
                'id': 'other_1',
                'title': 'Global Climate Summit Reaches Historic Agreement',
                'content': 'Representatives from 195 countries agreed on new climate targets and funding mechanisms for developing nations, marking a significant step in international climate cooperation.',
                'timestamp': '2025-08-19 16:20:00',
                'source': 'Associated Press'
            }
        ]
    }

if 'selected_article' not in st.session_state:
    st.session_state.selected_article = None

if 'reading_mode' not in st.session_state:
    st.session_state.reading_mode = False

if 'show_stats' not in st.session_state:
    st.session_state.show_stats = False

if 'dropdown_selection' not in st.session_state:
    st.session_state.dropdown_selection = ""

# 初始化一个排序版本号
if 'sort_version' not in st.session_state:
    st.session_state.sort_version = 0

# Helper functions
def get_article_by_id(article_id):
    for section, articles in st.session_state.articles.items():
        for article in articles:
            if article['id'] == article_id:
                return article, section
    return None, None

def get_article_by_title(title):
    for section, articles in st.session_state.articles.items():
        for article in articles:
            if article['title'] == title:
                return article, section
    return None, None

def reset_dropdown():
    st.session_state.dropdown_selection = ""

# Main UI
st.title("📰 Article Sequence Manager")

# Top control bar (mobile-friendly)
col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

with col1:
    if st.button("🔄 Reset", help="Reset to original order"):
        if 'multi_sort' in st.session_state:
            del st.session_state['multi_sort']
        st.session_state.reading_mode = False
        st.session_state.selected_article = None
        reset_dropdown()
        st.rerun()

with col2:
    if st.button("📊 Stats", help="Show/hide article statistics"):
        st.session_state.show_stats = not st.session_state.show_stats
        st.rerun()

with col3:
    # Build article list for reading
    all_articles = []
    article_id_to_title = {}
    for section in LOCATION_ORDER:
        for article in st.session_state.articles.get(section, []):
            short_title = f"{article['title'][:50]}..." if len(article['title']) > 50 else article['title']
            all_articles.append((short_title, article['id']))
            article_id_to_title[article['id']] = short_title
    
    if all_articles:
        article_options = ["Select article to read..."] + [title for title, _ in all_articles]
        
        # Set the index based on current selection
        if st.session_state.reading_mode and st.session_state.selected_article:
            current_title = article_id_to_title.get(st.session_state.selected_article, "")
            try:
                current_index = article_options.index(current_title)
            except ValueError:
                current_index = 0
        else:
            current_index = 0
        
        selected_title = st.selectbox(
            "📖", 
            article_options, 
            index=current_index,
            key="read_selector", 
            label_visibility="collapsed"
        )
        
        # Only trigger change if it's actually different and not the placeholder
        if (selected_title != "Select article to read..." and 
            selected_title != st.session_state.dropdown_selection):
            
            st.session_state.dropdown_selection = selected_title
            # Find the corresponding article ID
            for title, article_id in all_articles:
                if title == selected_title:
                    st.session_state.selected_article = article_id
                    st.session_state.reading_mode = True
                    st.rerun()

with col4:
    if st.button("📄 Generate Doc", help="Download organized document"):
        doc_content = f"# News Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        for section in LOCATION_ORDER:
            articles = st.session_state.articles.get(section, [])
            if articles:
                doc_content += f"## {section}\n\n"
                for i, article in enumerate(articles, 1):
                    doc_content += f"### {i}. {article['title']}\n"
                    doc_content += f"**Source:** {article['source']} | **Time:** {article['timestamp']}\n\n"
                    doc_content += f"{article['content']}\n\n"
                    doc_content += "---\n\n"
        
        st.download_button(
            label="📥 Download",
            data=doc_content,
            file_name=f"news_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            key="download_doc"
        )

# Show stats if toggled
if st.session_state.show_stats:
    st.markdown("### 📊 Article Statistics")
    stats_cols = st.columns(len([s for s in LOCATION_ORDER if st.session_state.articles.get(s, [])]))
    col_idx = 0
    total_articles = 0
    
    for section in LOCATION_ORDER:
        count = len(st.session_state.articles.get(section, []))
        if count > 0:
            with stats_cols[col_idx]:
                st.metric(section, count)
                col_idx += 1
            total_articles += count
    
    st.metric("Total Articles", total_articles)
    st.markdown("---")

# Article reading mode
if st.session_state.reading_mode and st.session_state.selected_article:
    article, section = get_article_by_id(st.session_state.selected_article)
    if article:
        st.markdown("### 📖 Reading Mode")
        
        # Close button
        if st.button("❌ Close Reading Mode", key="close_reading"):
            st.session_state.reading_mode = False
            st.session_state.selected_article = None
            reset_dropdown()
            st.rerun()
        
        # Article content
        st.markdown("---")
        st.markdown(f"## {article['title']}")
        
        # Article metadata in a more mobile-friendly layout
        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            st.markdown(f"**Section:** {section}")
            st.markdown(f"**Source:** {article['source']}")
        with meta_col2:
            st.markdown(f"**Time:** {article['timestamp']}")
        
        st.markdown("---")
        st.markdown(article['content'])
        st.markdown("---")
        
        # Another close button at the bottom for longer articles
        if st.button("❌ Close", key="close_reading_bottom"):
            st.session_state.reading_mode = False
            st.session_state.selected_article = None
            reset_dropdown()
            st.rerun()

else:
    # Main drag-and-drop interface
    st.markdown("### Current Article Sequence")
    st.info("💡 **Instructions:** Drag articles between sections to reorganize. Use the dropdown above to read articles.")
    
    # Prepare current items for sortable (include all sections, even empty)
    current_items = []
    for section in LOCATION_ORDER:
        section_items = [article['title'] for article in st.session_state.articles.get(section, [])]
        current_items.append({'header': section, 'items': section_items})
    
    # 使用动态 key，包含版本号
    # 这样每次 update 发生后，key 会改变，强制组件重新挂载（Remount），避免 React 更新死循环
    sort_key = f"multi_sort_{st.session_state.sort_version}"
    sorted_items = sort_items(current_items, multi_containers=True, direction='vertical', key=sort_key)
    
    # If order changed, update session state
    if sorted_items != current_items:
        updated_articles = {section: [] for section in LOCATION_ORDER}
        for container in sorted_items:
            section = container['header']
            if section in updated_articles:  # Ensure it's a valid section
                for title in container['items']:
                    article, _ = get_article_by_title(title)
                    if article:
                        updated_articles[section].append(article)
        st.session_state.articles = updated_articles

        # 增加排序版本号，确保下一次渲染时 key 变化
        st.session_state.sort_version += 1
        
        st.rerun()
    
    # Show empty sections info
    empty_sections = [s for s in LOCATION_ORDER if not st.session_state.articles.get(s, [])]
    if empty_sections:
        with st.expander("📋 Empty Sections (available for dragging)", expanded=False):
            st.write(", ".join(empty_sections))
